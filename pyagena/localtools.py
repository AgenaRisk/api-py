"""
Provisioning for the local agena.ai engine.

Until now `local_api_clone()` + `local_api_compile()` fetched the API's *source* from
public GitHub and built it with Maven, which meant every user needed git, Maven and a
JDK on PATH to produce an artifact we can publish once. The API source is now closed
and published as a pre-built runtime bundle instead, so this module downloads that
bundle and the two things it deliberately does not carry:

  * a JRE, so nothing depends on whatever Java the machine happens to have;
  * the Cryptlex licensing payload, which is product-specific, ~10 MB, shared by
    every API version, and therefore versioned and cached on its own.

Everything lands in ``~/.agena.ai/tools``, the same directory Athena uses, so a
machine with either installed already has most of what the other needs.

Nothing here writes into the working directory: the old code cloned ``./api`` next to
whatever the user was doing and ``cd``-ed into it to run Maven.
"""

import io
import json
import logging
import os
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
import zipfile
from sys import platform

import requests

# --------------------------------------------------------------------------------------
# Where things live
# --------------------------------------------------------------------------------------

#: Shared with Athena and any other local client. Override for tests or a sandbox.
TOOLS_DIR = os.environ.get(
    "AGENA_TOOLS_DIR", os.path.join(os.path.expanduser("~"), ".agena.ai", "tools")
)

#: Version-stamped, so switching Java majors actually takes effect on a machine that
#: already has another one. Unstamped, "is Java present" answered yes for any Java once
#: unpacked here, so a change of runtime would have been silently ignored on every
#: existing install — reaching new users only.
JRE_DIR = os.path.join(TOOLS_DIR, "jre")
LICENSING_DIR = os.path.join(TOOLS_DIR, "licensing")

REPO_RELEASE = "https://mvn.agenarisk.com/repository/internal"
REPO_SNAPSHOT = "https://mvn.agenarisk.com/repository/snapshots"
GROUP_ID = "com.agenarisk"
#: The engine. The API project was merged into core (ARC-324), so this is core's artifact.
ARTIFACT_ID = "com.agenarisk.core"
#: ``<tools>/core``: each artifact installs under its own directory, so the versions of
#: different artifacts, which mean nothing relative to each other, are never compared.
API_DIR = os.path.join(TOOLS_DIR, ARTIFACT_ID.rsplit(".", 1)[-1])

LICENSING_URL = "https://resources.agena.ai/download/archive/lib-v3.44.0.zip"
PRODUCT_URL = "https://resources.agena.ai/products/v3/developer/product.json"
JRE_BASE_URL = "https://resources.agena.ai/tools/jre"

#: Exact JRE build published on resources.agena.ai for each Java major.
#:
#: Which major to use is not this package's decision — it is the api jar's, read from
#: its manifest (see :func:`required_java_major`). This table only says which build of
#: that major we ship. A required major that is missing here raises, naming the version,
#: rather than falling back silently: running the engine on a runtime it did not ask for
#: is the failure this mechanism exists to prevent.
JRE_BUILDS = {
    21: "21.0.12.1_1",
    25: "25.0.4.1_1",
}

#: Archives re-hosted from another vendor because Adoptium publishes none.
#:
#: Keyed ``<major>-<os>-<arch>``. Temurin has no Windows ARM64 build for 25, though it
#: does for 21; Azul ships that platform at the same OpenJDK patch level, so the
#: substitution costs nothing and keeps every user on one engine version. The real
#: filename is kept rather than renamed to look like a Temurin build - the composed name
#: says ``hotspot``, and it would be a lie. Layout is not a concern: the extractor here
#: strips a single wrapper directory, which is what every vendor ships.
JRE_VENDOR_OVERRIDES = {
    "25-windows-aarch64": "zulu25.36.205-ca-jre25.0.4.1-win_aarch64.zip",
}

#: The Java major used when the jar states no requirement.
#:
#: Every jar built before ``Require-Java`` existed falls here. 21 rather than the
#: bytecode target: the jar is compiled with ``release 8``, so its class-file version
#: says "any JVM from 8 up", which is a floor and not a preference — honouring it
#: literally would install a Java 8 JRE nobody has tested against.
DEFAULT_JAVA_MAJOR = 21

#: How many API versions to keep. Enough to roll back, and to hold a snapshot beside
#: a release; past that they are only disk.
KEEP_VERSIONS = 3


# --------------------------------------------------------------------------------------
# Versions
# --------------------------------------------------------------------------------------

#: Versions below this major use the legacy fractional-minor scheme.
_SEMVER_FROM_MAJOR = 2


def _version_key(version):
    """
    Sort key that is correct for both API version schemes.

    Before 2.0.0 the API used ``major.minor`` where the minor was a three-digit
    *fraction*: ``1.03`` meant 1.030, and the series ran 0.1 … 1.043. Compared
    component-wise, ``0.98`` reads as [0, 98] and ``0.971`` as [0, 971], making 0.971
    look newer — but 0.98 meant 0.980 and is in fact newer. The published history has
    156 such pairs, so picking "the latest version" with a naive comparison really does
    resolve to the wrong artifact.

    Padding a two-component minor back out to the three digits it was written as fixes
    it. The switch to semver was deliberately made at a major boundary, so the two
    schemes only ever need telling apart, never reconciling: every 2.x.y outranks every
    1.x under either reading.
    """
    raw = re.sub(r"-SNAPSHOT$", "", version).split(".")
    out = []
    for part in raw:
        try:
            out.append(int(part))
        except ValueError:
            out.append(0)
    if len(raw) == 2 and out[0] < _SEMVER_FROM_MAJOR:
        try:
            out[1] = int(raw[1].ljust(3, "0"))
        except ValueError:
            out[1] = 0
    return out


def _repo_base(channel):
    if channel not in ("release", "snapshot"):
        raise ValueError("channel must be 'release' or 'snapshot'")
    repo = REPO_SNAPSHOT if channel == "snapshot" else REPO_RELEASE
    return "{}/{}/{}".format(repo, GROUP_ID.replace(".", "/"), ARTIFACT_ID)


def _get_text(url):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.text


def resolve_version(channel="release"):
    """
    Highest version published on a channel.

    Deliberately ignores ``<latest>`` in the metadata: Archiva leaves it stale — it
    still names a version from years ago — while ``<versions>`` is maintained. Maven's
    own tooling distrusts ``<latest>`` for the same reason.
    """
    try:
        xml = _get_text(_repo_base(channel) + "/maven-metadata.xml")
    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == 404:
            raise ValueError(
                "Nothing of {} is published on the {} channel yet.{}".format(
                    ARTIFACT_ID,
                    channel,
                    " Pass channel='snapshot' for unreleased builds." if channel == "release" else "",
                )
            ) from error
        raise
    versions = re.findall(r"<version>([^<]+)</version>", xml)
    if not versions:
        raise ValueError("No versions published on the {} channel".format(channel))
    return max((v.strip() for v in versions), key=_version_key)


def _bundle_name(base, version):
    """
    File name of the runtime bundle for a version.

    A release is named after its version; a snapshot is not, because Maven publishes
    each build under a timestamped name. That name is composed from ``<timestamp>`` and
    ``<buildNumber>`` rather than read from the more explicit ``<snapshotVersions>``
    list, because Archiva's repository scanner rewrites ``maven-metadata.xml`` and drops
    that list — so a resolver depending on it works right up until the first scan runs,
    then fails on artifacts that are still perfectly well there.
    """
    if not version.endswith("-SNAPSHOT"):
        return "{}-{}-runtime.zip".format(ARTIFACT_ID, version)

    xml = _get_text("{}/{}/maven-metadata.xml".format(base, version))
    timestamp = re.search(r"<timestamp>([^<]+)</timestamp>", xml)
    build_number = re.search(r"<buildNumber>([^<]+)</buildNumber>", xml)
    if timestamp and build_number:
        stem = re.sub(r"-SNAPSHOT$", "", version)
        return "{}-{}-{}-{}-runtime.zip".format(
            ARTIFACT_ID, stem, timestamp.group(1), build_number.group(1)
        )

    # Freshly deployed and not yet scanned: the explicit list is still present.
    for block in re.findall(r"<snapshotVersion>(.*?)</snapshotVersion>", xml, re.S):
        if "<classifier>runtime</classifier>" in block and "<extension>zip</extension>" in block:
            value = re.search(r"<value>([^<]+)</value>", block)
            if value:
                return "{}-{}-runtime.zip".format(ARTIFACT_ID, value.group(1))
    raise ValueError("No runtime bundle published for {}".format(version))


# --------------------------------------------------------------------------------------
# Download and unpack
# --------------------------------------------------------------------------------------


def _download(url, dest):
    with requests.get(url, stream=True, timeout=600) as response:
        response.raise_for_status()
        with open(dest, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1 << 20):
                handle.write(chunk)


def _common_root(names):
    """
    The single top-level directory shared by every entry, or None.

    Only a directory that contains *everything* is a wrapper. Stripping the first path
    segment unconditionally is the tempting version and it is wrong: given a bundle
    whose root holds a jar beside a ``lib/`` directory, it discards the jar and flattens
    the dependencies, while reporting success.
    """
    roots = set()
    for name in names:
        head = name.replace("\\", "/").split("/")[0]
        if not head:
            return None
        roots.add(head)
    if len(roots) != 1:
        return None
    root = roots.pop()
    return root if all(n.replace("\\", "/").startswith(root + "/") for n in names) else None


def _extract(archive_path, target):
    """Unpack an archive into ``target``, stripping a wrapper directory if there is one."""
    os.makedirs(target, exist_ok=True)

    if archive_path.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as archive:
            members = [m for m in archive.infolist() if not m.is_dir()]
            root = _common_root([m.filename for m in members])
            for member in members:
                name = member.filename.replace("\\", "/")
                if root:
                    name = name[len(root) + 1 :]
                out_path = os.path.join(target, *name.split("/"))
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with archive.open(member) as source, open(out_path, "wb") as sink:
                    shutil.copyfileobj(source, sink)
                # Zip carries unix permissions in the high bits of external_attr, and
                # the JRE's `java` is unusable without its executable bit.
                mode = member.external_attr >> 16
                if mode:
                    os.chmod(out_path, mode)
        return

    with tarfile.open(archive_path, "r:*") as archive:
        members = [m for m in archive.getmembers() if m.isfile() or m.issym()]
        root = _common_root([m.name for m in members])
        for member in members:
            name = member.name.replace("\\", "/")
            if root:
                name = name[len(root) + 1 :]
            member.name = name
            archive.extract(member, target)


def _install_archive(url, target, expected, force=False):
    """Download and unpack an archive unless ``expected`` is already present."""
    if not force and all(os.path.exists(p) for p in expected):
        return False

    name = url.split("/")[-1]
    shutil.rmtree(target, ignore_errors=True)
    tmp = os.path.join(tempfile.gettempdir(), name)
    logging.info("Downloading %s", url)
    _download(url, tmp)
    try:
        _extract(tmp, target)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass

    missing = [p for p in expected if not os.path.exists(p)]
    if missing:
        shutil.rmtree(target, ignore_errors=True)
        raise ValueError("{} did not contain {}".format(name, ", ".join(missing)))
    return True


# --------------------------------------------------------------------------------------
# Java
# --------------------------------------------------------------------------------------


_required_major_cache = {}


def required_java_major(jar=None):
    """
    Java major the installed api jar asks for, or the default when it says nothing.

    Read from the jar's ``Require-Java`` manifest attribute. The jar is the only thing
    that knows which runtime it was built and tested for, so it says so and clients
    obey — rather than each client pinning a version of its own and hoping they agree.
    """
    jar = jar or jar_path()
    if not jar or not os.path.exists(jar):
        return DEFAULT_JAVA_MAJOR
    if jar in _required_major_cache:
        return _required_major_cache[jar]

    major = DEFAULT_JAVA_MAJOR
    try:
        with zipfile.ZipFile(jar) as archive:
            manifest = archive.read("META-INF/MANIFEST.MF").decode("utf-8", "replace")
        # Manifest lines wrap at 72 bytes with a leading space on continuations; a bare
        # major never wraps, so a simple match is safe here.
        match = re.search(r"^Require-Java:\s*(\d+)", manifest, re.M)
        if match:
            major = int(match.group(1))
    except (OSError, KeyError, zipfile.BadZipFile):
        # An unreadable manifest is not worth failing over: the default is a runtime
        # this jar can load, since the floor has only ever gone up from 8.
        pass
    _required_major_cache[jar] = major
    return major


def _jre_build(major):
    build = JRE_BUILDS.get(major)
    if build is None:
        raise ValueError(
            "The agena.ai API requires Java {}, which this version of pyagena does not "
            "know how to install. Upgrade pyagena, or upload that JRE to {}/{}/ and add "
            "it to JRE_BUILDS.".format(major, JRE_BASE_URL, major)
        )
    return build


def java_dir(major=None):
    """Install directory for the JRE of a given Java major."""
    return os.path.join(JRE_DIR, _jre_build(major or required_java_major()))


def _java_home(major=None):
    # A macOS JRE archive is a bundle; the runtime sits inside Contents/Home.
    base = java_dir(major)
    return os.path.join(base, "Contents", "Home") if platform == "darwin" else base


def java_path(major=None):
    """Path to the managed ``java`` executable, whether or not it exists yet."""
    return os.path.join(
        _java_home(major), "bin", "java.exe" if platform == "win32" else "java"
    )


def _os_arch():
    machine = os.uname().machine.lower() if hasattr(os, "uname") else os.environ.get(
        "PROCESSOR_ARCHITECTURE", ""
    ).lower()
    arch = "aarch64" if machine in ("arm64", "aarch64") else "x64"
    if platform == "win32":
        return "windows", arch, "zip"
    if platform == "darwin":
        return "mac", arch, "tar.gz"
    if platform.startswith("linux"):
        return "linux", arch, "tar.gz"
    raise ValueError("Unsupported platform: {}".format(platform))


def _jre_archive_name(major):
    system, arch, ext = _os_arch()
    # A vendor override wins over the composed Adoptium name, for platforms Adoptium
    # does not publish at all.
    override = JRE_VENDOR_OVERRIDES.get("{}-{}-{}".format(major, system, arch))
    if override:
        return override
    return "OpenJDK{}U-jre_{}_{}_hotspot_{}.{}".format(
        major, arch, system, _jre_build(major), ext
    )


def system_java():
    """
    The machine's own ``java`` and its major version, or ``(None, 0)``.

    A system Java is the fallback for platforms no JRE is published for, but it has to
    be asked its version rather than assumed usable: a Java 17 cannot load a jar built
    for 21, and taking whatever is on the PATH turns a clear setup failure into an
    ``UnsupportedClassVersionError`` part-way through a calculation.
    """
    found = shutil.which("java")
    if not found:
        return None, 0
    try:
        completed = subprocess.run(
            [found, "-version"], capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return found, 0
    # `java -version` writes to stderr, and reports either 1.8.0_x for 8 and below or
    # 21.0.12.1 from 9 on, so a leading "1." has to be stripped before the first
    # component means the major.
    text = (completed.stderr or "") + (completed.stdout or "")
    match = re.search(r'version "([0-9._]+)', text)
    if not match:
        return found, 0
    parts = match.group(1).split(".")
    try:
        return found, int(parts[1] if parts[0] == "1" else parts[0])
    except (IndexError, ValueError):
        return found, 0


def resolve_java(major=None):
    """
    The ``java`` to run this jar with: ours if installed, else a new enough system one.

    Accepted on ``>=`` rather than equality - a newer runtime satisfies the floor, and
    refusing Java 26 when the jar asked for 25 would be unhelpfully strict.
    """
    major = major or required_java_major()
    try:
        ours = java_path(major)
    except ValueError:
        ours = None
    if ours and os.path.exists(ours):
        return ours

    found, found_major = system_java()
    if found and found_major >= major:
        logging.info("Using the Java %s already on this machine (%s)", found_major, found)
        return found
    return None


def install_java(major=None, force=False):
    """
    Install the JRE the api jar asks for.

    A JRE, not a JDK: nothing is compiled at runtime any more, so the compiler was only
    ever needed by the Maven build that no longer happens. That takes the download from
    roughly 180 MB to 47 MB.
    """
    major = major or required_java_major()
    try:
        name = _jre_archive_name(major)
    except ValueError:
        # A Java we cannot download is only a problem if the machine has no suitable one
        # of its own. Where it does, the engine runs on that instead.
        found, found_major = system_java()
        if found and found_major >= major:
            logging.info(
                "No Java %s runtime is published for pyagena to install; using the "
                "Java %s already on this machine (%s)",
                major, found_major, found,
            )
            return False
        raise
    # JREs are served per major: <base>/21/<archive>, <base>/25/<archive>. A flat
    # directory would make two majors of the same product indistinguishable by path.
    installed = _install_archive(
        "{}/{}/{}".format(JRE_BASE_URL, major, name),
        java_dir(major),
        [java_path(major)],
        force=force,
    )
    if installed:
        os.chmod(java_path(major), os.stat(java_path(major)).st_mode | stat.S_IEXEC)
        logging.info("Java %s installed to %s", _jre_build(major), java_dir(major))
    return installed


# --------------------------------------------------------------------------------------
# Licensing payload
# --------------------------------------------------------------------------------------


def _licensing_version():
    # The archive name is the only place this version is recorded. Stamping the install
    # directory with it means a Cryptlex upgrade cannot half-overwrite the payload in use.
    match = re.search(r"lib-v([0-9.]+)\.zip$", LICENSING_URL)
    return match.group(1) if match else "unversioned"


def licensing_path():
    """Directory holding the Cryptlex natives and the product file."""
    return os.path.join(LICENSING_DIR, _licensing_version())


def install_licensing(force=False):
    """Install the Cryptlex natives, then the product file that identifies the product."""
    target = licensing_path()
    if not force and os.path.exists(os.path.join(target, "product.json")):
        return False

    _install_archive(
        LICENSING_URL, target, [os.path.join(target, "lexactivator3")], force=True
    )
    # Published separately from the natives archive because that archive is
    # product-agnostic and this file is precisely what is not.
    response = requests.get(PRODUCT_URL, timeout=60)
    response.raise_for_status()
    with open(os.path.join(target, "product.json"), "wb") as handle:
        handle.write(response.content)
    logging.info("Licensing components installed to %s", target)
    return True


# --------------------------------------------------------------------------------------
# The API bundle
# --------------------------------------------------------------------------------------


#: Written into each install's directory: which build of the version it is. The same
#: file and fields Athena writes (ApiDownloader.STAMP_FILE), as the directory is shared.
STAMP_FILE = ".install.json"

#: Names the directory of the build in use, not its version. Read by Athena and the bench
#: too.
CURRENT_FILE = "current"

#: A new build being unpacked, and a pruned one awaiting removal. Both sit beside the
#: installs, and the leading dot keeps them out of the installs.
STAGING_PREFIX = ".staging-"
RETIRED_PREFIX = ".retired-"

#: How long moving a new build into place keeps retrying a rename that something is
#: briefly blocking.
RENAME_RETRY_SECONDS = 5


def _current_folder():
    """The directory name ``current`` holds, or None when nothing is installed."""
    try:
        with open(os.path.join(API_DIR, CURRENT_FILE)) as handle:
            return handle.read().strip() or None
    except OSError:
        return None


def installed_path():
    """Directory of the installed API, or None."""
    folder = _current_folder()
    if folder is None:
        return None
    directory = os.path.join(API_DIR, folder)
    return directory if os.path.isdir(directory) else None


def _read_stamp(directory):
    """The stamp in an install directory, or None when it has none."""
    try:
        with open(os.path.join(directory, STAMP_FILE)) as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def installed_version():
    """
    Version of the installed API, or None.

    From the stamp, since the directory name carries the build too
    (``2.0.0-SNAPSHOT-34``, or ``2.0.0-SNAPSHOT-34-r2`` for a reinstall of it); an install
    from before stamps existed is named after its version alone.
    """
    directory = installed_path()
    if directory is None:
        return None
    return (_read_stamp(directory) or {}).get("version") or os.path.basename(directory)


def _build_of(bundle):
    """``(timestamp, buildNumber)`` of a snapshot bundle's file name; ``(None, None)`` for a release."""
    match = re.search(r"-(\d{8}\.\d{6})-(\d+)-runtime\.zip$", bundle)
    return (match.group(1), match.group(2)) if match else (None, None)


def installed_stamp():
    """The installed build's stamp (version, channel, timestamp, buildNumber), or ``{}``."""
    directory = installed_path()
    return (_read_stamp(directory) if directory else None) or {}


def _is_engine_jar(name):
    return name.endswith(".jar") and "-javadoc" not in name and "-sources" not in name


def jar_path():
    """Path to the installed API jar, or None if the API is not installed."""
    directory = installed_path()
    if directory is None:
        return None
    for name in sorted(os.listdir(directory)):
        if _is_engine_jar(name):
            return os.path.join(directory, name)
    return None


def _iso_time(seconds=None):
    """UTC time in the form Athena stamps (``2026-10-22T15:09:30.913Z``), so they sort together."""
    seconds = time.time() if seconds is None else seconds
    return "{}.{:03d}Z".format(
        time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(seconds)), int(seconds * 1000) % 1000
    )


def _build_folder_name(version, timestamp, build_number):
    """
    The directory a build installs into: a release under its version, a snapshot under
    its version and build number, since every push republishes ``2.0.0-SNAPSHOT``.
    """
    if not version.endswith("-SNAPSHOT"):
        return version
    return "{}-{}".format(version, build_number or timestamp or int(time.time() * 1000))


def _free_folder_name(name):
    """
    ``name``, or ``name-r2``, ``name-r3``... when a directory of that name exists.
    Reinstalling the build already in use is the case: its directory may be a running
    engine's, so it is left alone and the reinstall goes beside it.
    """
    candidate, n = name, 2
    while os.path.exists(os.path.join(API_DIR, candidate)):
        candidate = "{}-r{}".format(name, n)
        n += 1
    return candidate


def _rename_retrying(source, destination):
    """
    Rename, retrying while Windows reports the path in use: a virus scanner reading the
    newly unpacked files clears in a moment.
    """
    until = time.time() + RENAME_RETRY_SECONDS
    while True:
        try:
            os.rename(source, destination)
            return
        except FileExistsError:
            raise
        except PermissionError:
            if time.time() > until:
                raise
        except OSError as error:
            # 32: ERROR_SHARING_VIOLATION, which Python does not map to PermissionError.
            if getattr(error, "winerror", None) != 32 or time.time() > until:
                raise
        time.sleep(0.25)


def _remove_tree(directory):
    """Best effort: a directory that cannot be removed now is removed by the next install."""
    shutil.rmtree(directory, ignore_errors=True)


def _remove_leftovers():
    """Staging and retired directories an interrupted install left behind."""
    try:
        for name in os.listdir(API_DIR):
            if name.startswith(STAGING_PREFIX) or name.startswith(RETIRED_PREFIX):
                _remove_tree(os.path.join(API_DIR, name))
    except OSError:
        # Housekeeping, like pruning: never a reason to fail an install.
        pass


def _looks_like_install(directory):
    """Whether a directory holds an installed bundle, rather than being some other thing."""
    try:
        if os.path.exists(os.path.join(directory, STAMP_FILE)):
            return True
        # Installs made before stamps existed still have the jar at their root, which
        # other directories here (the bench's ``build/``) do not.
        return any(_is_engine_jar(name) for name in os.listdir(directory))
    except OSError:
        return False


def _prune_old_builds():
    """
    Keep the newest build of each of the newest KEEP_VERSIONS versions, plus whatever is
    current; older builds of a version are superseded outright.

    The previous build's directory may still be in use by an engine started from it
    (Athena's engine service, or another script). It is renamed aside before it is
    deleted, because a rename is refused whole while a jar inside is open, where a delete
    stops part way. A directory still in use is left for a later install.
    """
    try:
        installs = []
        for name in os.listdir(API_DIR):
            directory = os.path.join(API_DIR, name)
            if name.startswith(".") or not os.path.isdir(directory):
                continue
            if not _looks_like_install(directory):
                continue
            stamp = _read_stamp(directory) or {}
            installs.append(
                (
                    directory,
                    stamp.get("version") or name,
                    stamp.get("installedAt") or _iso_time(os.path.getmtime(directory)),
                )
            )

        newest_build = {}
        for directory, version, installed_at in installs:
            seen = newest_build.get(version)
            if seen is None or installed_at > seen[1]:
                newest_build[version] = (directory, installed_at)
        newest_versions = sorted(newest_build, key=_version_key, reverse=True)
        keep = {newest_build[v][0] for v in newest_versions[:KEEP_VERSIONS]}
        current = _current_folder()
        if current:
            keep.add(os.path.join(API_DIR, current))

        for directory, _, _ in installs:
            if directory in keep:
                continue
            name = os.path.basename(directory)
            retired = os.path.join(
                API_DIR,
                "{}{}-{}-{}".format(RETIRED_PREFIX, name, os.getpid(), int(time.time() * 1000)),
            )
            try:
                os.rename(directory, retired)
            except OSError as error:
                logging.info("Kept superseded API install %s for now: %s", name, error)
                continue
            _remove_tree(retired)
            logging.info("Removed superseded API install %s", name)
    except OSError as error:
        # Housekeeping: failing to prune must never fail an install.
        logging.info("Could not prune old API installs: %s", error)


def channel_of(version):
    """Which channel a version came from, judged from the version string itself."""
    return "snapshot" if version.endswith("-SNAPSHOT") else "release"


def install_api(channel=None, version=None, update=False, force=False):
    """
    Install the API runtime bundle, or confirm that one is already installed.

    Does nothing when the API is present and no change was asked for — and in that case
    does not touch the network at all, so this is safe to call at the top of a script
    that runs daily. Left to resolve the newest version every time, it would upgrade the
    engine underneath the caller: two runs of the same script could use two different
    engines, which is exactly what a reproducible analysis must not do. An upgrade is
    therefore something you ask for, never something that happens to you.

    Releases only, unless snapshots are asked for: ``channel="snapshot"``, or ``version``
    pinning a snapshot version. Without either, the channel is ``"release"`` whatever is
    installed, so a snapshot is never picked up by accident.

    A change is being asked for when ``update`` is set (resolve the channel's newest and
    install it if it is newer), when ``version`` names something other than what is
    installed, when the channel differs from the one the installed version came from
    (so with a snapshot installed, a call without ``channel="snapshot"`` moves to the
    newest release), or when ``force`` is set.

    Each build installs into a directory of its own — ``<tools>/core/<version>/`` for a
    release, ``<tools>/core/<version>-<build>/`` for a snapshot, with ``-r2``, ``-r3``...
    added when that directory exists — and ``current`` names the one in use. Nothing
    installed is touched, since an engine running from it holds its jars open: on
    Windows such a directory can be neither deleted nor renamed. The layout is Athena's
    (ApiDownloader), as the directory is shared.
    """
    installed = installed_version()
    channel = channel or (channel_of(version) if version else "release")

    if installed is not None and not force:
        asked = (
            update
            or (version is not None and version != installed)
            or channel_of(installed) != channel
        )
        if not asked:
            logging.info(
                "Using API %s. Call local_api_install(update=True) to check for a newer one",
                installed,
            )
            return installed

    base = _repo_base(channel)
    if version is None:
        version = resolve_version(channel)
    name = _bundle_name(base, version)
    timestamp, build_number = _build_of(name)
    # A snapshot keeps its version across every build, so the version alone cannot say
    # whether the install is current: compare the build too.
    stamp = installed_stamp()
    if not force and installed == version and (
        timestamp is None
        or (stamp.get("timestamp") == timestamp and stamp.get("buildNumber") == build_number)
    ):
        logging.info("API %s is already the newest on the %s channel", version, channel)
        return version

    os.makedirs(API_DIR, exist_ok=True)
    _remove_leftovers()
    folder = _free_folder_name(_build_folder_name(version, timestamp, build_number))
    target = os.path.join(API_DIR, folder)
    # Unpacked under a staging name so a half-written build never looks installed.
    staging = os.path.join(
        API_DIR,
        "{}{}-{}-{}".format(STAGING_PREFIX, version, os.getpid(), int(time.time() * 1000)),
    )
    try:
        try:
            _install_archive("{}/{}/{}".format(base, version, name), staging, [], force=True)
        except requests.HTTPError as error:
            # A version can resolve perfectly well and still have no bundle: releases
            # made before the runtime bundle existed publish only a bare jar. Saying so
            # beats handing back a 404 and a URL.
            if error.response is not None and error.response.status_code == 404:
                raise ValueError(
                    "The {} channel's newest version, {}, has no runtime bundle. Releases "
                    "made before this distribution format publish only a bare jar. Try "
                    "local_api_install(channel='snapshot').".format(channel, version)
                ) from error
            raise
        if not any(_is_engine_jar(f) for f in os.listdir(staging)):
            raise ValueError("The bundle for {} contained no jar".format(version))

        with open(os.path.join(staging, STAMP_FILE), "w") as handle:
            json.dump(
                {
                    "version": version,
                    "channel": channel,
                    "timestamp": timestamp,
                    "buildNumber": build_number,
                    "installedAt": _iso_time(),
                },
                handle,
                indent=2,
            )
        try:
            _rename_retrying(staging, target)
        except OSError as error:
            raise ValueError(
                "Could not put the engine {} in place ({}); the installed engine is "
                "unchanged".format(version, error)
            ) from error
    finally:
        _remove_tree(staging)

    # Last, so until here the previous build is the installed one in every respect.
    with open(os.path.join(API_DIR, CURRENT_FILE), "w") as handle:
        handle.write(folder)
    logging.info(
        "Installed API %s%s from the %s channel to %s",
        version,
        " build {}".format(build_number) if build_number else "",
        channel,
        target,
    )

    _prune_old_builds()
    return version


# --------------------------------------------------------------------------------------
# Public entry point and command construction
# --------------------------------------------------------------------------------------


def local_api_install(channel=None, version=None, update=False, force=False):
    """
    Make sure everything needed to run the engine locally is present: a JRE, the
    licensing payload and the API runtime bundle.

    Safe to call at the top of a script. Anything already installed on the channel asked
    for is left exactly as it is, no network request is made, and it returns quickly —
    so a script that starts with this line works on a fresh machine and stays on one
    engine version thereafter. Upgrading is opt-in: pass ``update=True``. The channel is
    ``"release"`` unless ``channel="snapshot"`` is passed.

    Replaces ``local_api_clone()`` and ``local_api_compile()``. There is no git, Maven
    or JDK involved, nothing is written to the working directory, and the result is
    shared with any other agena.ai client on the machine.

    :param channel: ``"release"`` (the default) or ``"snapshot"`` for unreleased builds.
        Snapshots are used only when asked for here or by pinning a snapshot ``version``;
        with a snapshot installed, a call without it moves to the newest release.
    :param version: pin an exact version instead of resolving the newest.
    :param update: check the channel for a newer version and install it if there is one.
    :param force: reinstall even if the components are already present.
    :returns: the API version now installed.
    """
    # The API comes first: the jar states which Java runtime it needs, so there is
    # nothing to resolve a JRE against until it is on disk. Downloading and unpacking
    # the bundle needs no Java itself, so the order costs nothing.
    installed = install_api(channel=channel, version=version, update=update, force=force)
    install_java(force=force)
    install_licensing(force=force)
    return installed


def _require_installed():
    jar = jar_path()
    if jar is None:
        raise ValueError(
            "The local agena.ai API is not installed. Run pyagena.local_api_install()"
        )
    java = resolve_java()
    if java is None:
        major = required_java_major()
        raise ValueError(
            "No Java {} or newer is available to run the agena.ai API. Run "
            "pyagena.local_api_install(), or install a Java {} runtime - Azul Zulu and "
            "BellSoft Liberica publish platforms Adoptium does not".format(major, major)
        )
    if not os.path.exists(os.path.join(licensing_path(), "product.json")):
        raise ValueError(
            "The licensing components are not installed. Run pyagena.local_api_install()"
        )
    return jar, java


def engine_command(args, working_directory=None):
    """
    Full argv for one engine invocation.

    ``java -jar`` rather than ``mvn exec:java``, which means no shell and so no hand
    quoting — the old code built one command string for PowerShell and another for sh,
    and the model path had to survive both. It also means the product and native-library
    directories have to be passed explicitly: both default to ``./lib`` relative to the
    working directory, which under Maven happened to be the API project and now is not.
    """
    jar, java = _require_installed()
    return [
        java,
        "-jar",
        jar,
        *args,
        "--directoryProduct",
        licensing_path(),
        "--directoryNativeLibs",
        licensing_path(),
        "--directoryWorking",
        working_directory or os.getcwd(),
    ]

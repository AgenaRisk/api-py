# Table of Contents

* [Description](#1-description)
* [Prerequisites and Installation](#2-prerequisites-and-installation)
* [Structure of pyagena Classes](#3-structure-of-pyagena-classes)
* [Class and Instance Methods](#4-class-and-instance-methods)
* [Importing a Model from .cmpx](#5-importing-a-model-from-cmpx)
* [Creating and Modifying a Model in python](#6-creating-and-modifying-a-model-in-python)
* [Creating Batch Cases for a Model in python](#7-creating-batch-cases-for-a-model-in-python)
* [Agena.ai Cloud with pyagena](#8-agenaai-cloud-with-pyagena)
* [Local agena.ai API with pyagena](#9-local-agenaai-api-with-pyagena)
* [pyagena Use Case Examples](#10-pyagena-use-case-examples)

# 1. Description

pyagena is a python environment for creating, modifying, and parsing Bayesian network models, and sending the models to agena.ai Cloud or to local agena.ai developer API to execute calculation requests. The environment allows users to read and modify Bayesian networks from .cmpx model files, create new Bayesian networks in python and export to .cmpx and .json files locally, as well as authenticate with agena.ai Cloud or use local agena.ai developer API for model calculations and sensitivity analyses. In the rest of this document, the python environment for agena.ai is referred to as pyagena. pyagena is developed for Python 3.

# 2. Prerequisites and Installation

FOR NOW:

To use pyagena, clone the repository and open a terminal in the directory to locally install the package using pip

```bash
pip install .
```
Here `.` installs all the packages in the directory.

To use pyagena, create a new python script (or a jupyter notebook file) and import the package

```python
import pyagena
```

or

```python
from pyagena import *
```

[ONLY FOR NOW, FOR TESTING PURPOSES - WHEN WE'RE DONE IT WILL BE UPLOADED TO PIP SO USERS CAN INSTALL THE PACKAGE WITHOUT CLONING THE REPO]

pyagena requires the following python packages to be installed: `requests`, `pandas`, `networkx`, and `matplotlib`

To install the dependencies, you can use [pip](https://pypi.org/project/pip/) with the commands:

```bash
pip install requests
pip install pandas
pip install matplotlib
pip install networkx
```

System packages used in pyagena: `sys`, `os`, `tempfile`, `json`, `getpass`, `time`, and `subprocess` (just for your information, not needed to install explicitly)

# 3. Structure of pyagena Classes

The Bayesian networks (BNs) in pyagena are represented with several objects: `Node`, `Network`, `Dataset`, and `Model`. These python objects generally follow their equivalents defined in agena.ai models.

## 3.1 `Node` objects

These represent the nodes in a BN. The fields that define a `Node` object are as follows:

### 3.1.1 `id`

Mandatory field to create a new `Node` object. This is the unique identifier of agena.ai model nodes.

### 3.1.2 `name`

Name of the node, optional. If not defined, `id` of the node will be passed onto the `name` field too.

### 3.1.3 `description`

Description of the node, optional. If not defined, "New Node" will be assigned to the `description` field.

### 3.1.4 `type`

Node type, it can be:

* Boolean
* Labelled
* Ranked
* DiscreteReal
* ContinuousInterval
* IntegerInterval

If it's not specified when creating a new node, the new node is "Boolean" by default if it's not a simulation node; and it is "ContinuousInterval" by default if it's a simulation node.

### 3.1.5 `parents`

Other `Node` objects can be pointed as parents of a `Node` object. It is not recommended to modify this field manually, to add parents to a node, see the function `add_parent()`.

Something to keep in mind: the parent-child relationship information is stored at `Node` level in the python environment thanks to this field, as opposed to the separate `links` field of a .cmpx/.json file for the agena.ai models. When importing or exporting .cmpx files you do not need to think about this difference, as the cmpx parser and writer functions handle the correct formats. This difference allows adding and removing `Node` objects as parents.

### 3.1.6 `simulated`

A boolean field to indicate whether the node is a simulation node or not.

### 3.1.7 `distr_type`

The table type of the node, it can be:

* Manual
* Expression
* Partitioned

### 3.1.8 `states`

States of the node (if not simulated). If states are not specified, depending on the `type`, sensible default states are assigned. Default states for different node types are:

* "Boolean" or "Labelled" node: "False", "True"
* "Ranked" node: "Low", "Medium", "High"
* "DiscreteReal" node: "0", "1"
* "IntegerInterval" node (if not simulated): "(-Infinity, -1]", "[0, 4]", "[5, Infinity)"
* "ContinuousInterval" node (if not simulated): "(-Infinity, -1)", "[-1, 1)", "[1, Infinity)"

And for a node with the table type (`distr_type`) "Expression", the default expression is: "Normal(0,1000000)"

### 3.1.9 `probabilities`

If the table type (`distr_type`) of the node is "Manual", the node will have state probabilities, values in its NPT. This field is a list of lists containing these values. The length of the list depends on the node states and the number of its parents. To see how to set probability values for a node, see `set_probabilities()` function. 

### 3.1.10 `expressions`

If the table type (`distr_type`) of the node is "Expression" or "Partitioned", the node will have expression(s) instead of the manually defined NPT values.

* If the node's table type is "Expression", the `expressions` field will be a list with a single expression.
* If the node's table type is "Partitioned", the `expressions` field will be a list of as many expressions as the number of parent node states on which the expression is partitioned.

To see how to set the expressions for a node, see `set_expressions()` function.

Possible expressions for the node types are listed below:

Boolean and Labelled:
* Comparative

IntegerInterval
* Binomial
* Exponential 
* Geometric 
* Hypergeometric 
* Negative Binomial 
* Normal 
* Poisson 
* TNormal 
* Triangular 
* Uniform 

ContinuousInterval
* Arithmetic
* Beta
* BetaPert
* ChiSquared
* Exponential
* ExtremeValue
* Gamma
* Logistic
* LogNormal
* Normal
* Student
* TNormal
* Triangle
* Uniform
* Weibull

Ranked
* TNormal

For further information on expressions, please refer to [agena.ai modeller manual, Sections 22 (Statistical distributions) and 23 (Expressions)](https://resources.agena.ai/materials/AgenaRisk%2010%20Desktop%20User%20Manual.pdf).

### 3.1.11 `partitions`

If the table type (`distr_type`) of the node is "Partitioned", in addition to the expressions, the node will have the `partitions` field. This field is a list of strings, which are `id`s of the parent nodes on which the node expression is partitioned.

### 3.1.12 `variables`

The node variables are called constants on agena.ai Modeller. This field, if specified, sets the constant value for the node observations. For the correct syntax of defining a variable, see `set_variable()` function.

## 3.2 `Network` objects 

These represent each network in a BN. Networks consist of nodes and in a BN model there might be more than one network. These networks can also be linked to each other with the use of input and output nodes. For such links, see `Model.network_links` field later in this document.

The fields that define a `Network` object are as follows:

### 3.2.1 `id`

Id of the `Network`. Mandatory field to create a new network.

### 3.2.2 `name`

Name of the network, optional. If not specified, `id` of the network is passed onto `name` field as well.

### 3.2.3 `description`

Description, optional. If not specified, the string "New Network" is assigned to `description` field by default.

### 3.2.4 `nodes`

A list of `Node` objects which are in the network. These `Node` objects have their own fields which define them as explained above in this document.

Note that `Network` objects do not have a `links` field unlike the agena.ai models. As explained in `Node.parents` section above, this information is stored in `Node` objects in the python environment. When importing a .cmpx model, the information in `links` field is used to populate `Node.parents` fields for each node. Similarly, when exporting to a .cmpx/.json file, the parent-child information in `Node.parents` field is used to create the `links` field of the `Network` field of the .cmpx/.json.

## 3.3 `Dataset` objects 

These represent the set of observations in a BN (cases). A `Model` can have multiple `Dataset` objects in its `datasets` field.  When a new `Model` is created, it always comes with a default `Dataset` object with the `id` "Case 1" and with blank observations. It is possible to add more datasets (cases) with their `id`s. Each `Dataset` object under a `Model` can be called a new "case".

### 3.3.1 `id`

Id of the dataset (case).

### 3.3.2 `observations`

Under each dataset (case), observations for all the observed nodes in all the networks of the model (in terms of their states or values) are listed. If it's hard evidence, observation for a node will have a single value with the weight of 1. If a node in the model has a value in its `variable` field, this value will be passed onto the dataset (case) with the weight of 1.

### 3.3.3 `results`

This field is defined only for when a .cmpx model with calculations is imported or after the model is calculated with the agena.ai Cloud or local API. When creating a new BN in the python environment, this field is not filled in. The `results` field stores the posterior probability and inference results upon model calculation on agena.ai Cloud or local agena.ai developer API.

## 3.4 `Model` objects

These represent the overall BN. A single .cmpx file corresponds to a singe `Model`. A BN model can have multiple networks with their own nodes, links between these networks, and datasets. 

## 3.4.1 `id`

Id of the Model, optional. If not specified, the `id` of the first `Network` in the model's `networks` field is used to create a `Model.id`. 

## 3.4.2 `networks`

A list of all the `Network` objects that make up the model. This field is mandatory for creating a new `Model` object. 

## 3.4.3 `datasets`

Optional field for `Dataset` objects. When creating a new `Model`, it is possible to use predefined cases as long as their `DataSet.observations` field has matching `id`s with the nodes and networks in the model. If none is specified, by default a new `Model` object will come with an empty dataset called "Case 1", and new datasets (cases) can be added afterwards.

## 3.4.4 `network_links`

If the `Model` has multiple networks, it is possible to have links between these networks, following the agena.ai model network_links format.

To see how to create these links, see `add_network_link()` function later in this document.

## 3.4.5 `settings`

`Model` settings for calculations. It includes the following fields (the values in parantheses are the defaults if settings are not specified for a model):

* discreteTails (False)
* sampleSizeRanked (5)
* convergence (0.01)
* iterations (50)
* tolerance (1)

Model settings can be provided when creating a new model, if not provided the model will come with the default settings. Default settings can be changed later on (with the method `change_settings()`), or model settings can be reset back to default values (with the method `default_settings()`). See the correct input parameter format for these functions in the following section. Individual fields in model setting can be adjusted with `change_settings()` too.

# 4. Class and Instance Methods

The `Node`, `Network`, and `Model` objects have their own respective methods to help their definition and manipulate their fields. The python instance methods are used with the `.` sign following an instance of the class. For example,

```python
example_node.add_parent(example_parent_node)
```

or

```python
example_network.remove_node(example_node)
```

or

```python
example_model.create_dataset(example_case)
```

## 4.1 `Node` methods

Some `Node` fields can be modified with a direct access to the field. For example, to update the name or a description information of a `Node`, simply use:

```python
example_node.name = "new node name"
```

or

```python
example_node.description = "new node description"
```

Because changing the name or description of a `Node` does not cause any compatibility issues. However, some fields such as table type or parents will have implications for other fields. Changing the node parents will change the size of its NPT, changing the node's table type from "Manual" to "Expression" will mean the state probabilities are now defined in a different way. Therefore, to modify such fields of a `Node`, use the corresponding method described below. These methods will ensure all the sensible adjustments are made when a field of a `Node` has been changed.

These are the methods `Node` objects can call for various purposes with their input parameters shown in parantheses:

### 4.1.1 `set_states(states)`

The method to update the states of the `Node` object. The node states can be defined upon creation if the node is a discrete node. If states are not specified during creation, sensible defaults will be assigned based on the node type. With `set_states()` it is possible to update node states later on. If the number of new states given with this method is the same as the previous number of node states, state names will be updated. If `set_states()` changes the number of node states, node probability table size will be adjusted accordingly and probability values will reset to uniform.

### 4.1.2 `add_parent(new_parent)`

The method to add a new parent to a node. Equivalent of adding an arc between two nodes on agena.ai Modeller. The input parameter `new_parent` is another `Node` object. If `new_parent` is already a parent for the node, the function does not update the `parents` field of the node.

When a new parent is added to a node, its NPT values and expressions are reset/resized accordingly. 

### 4.1.3 `remove_parent(old_parent)` 

The method to remove one of the existing parents of a node. Equivalent of removing the arc between two nodes on agena.ai Modeller. The input parameter `old_parent` is a `Node` object which has already been added to the `parents` field of the node.

When an existing parent is removed from a node, its NPT values and expressions are reset/resized accordingly.

### 4.1.4 `set_distr_type(new_distr_type)`

A method to set the table type (`distr_type`) of a node. If a `Node` is `simulated`, its table type can be "Expression" or "Partitioned" - the latter is only if the node has discrete parent nodes. If a `Node` is `not simulated`, its table type can be "Manual", "Expression", or "Partitioned (if the node has discrete parent nodes)".

Changing the node's distribution type (table type) adjusts its `states`/`probabilities`/`expressions`` parameters accordingly.

### 4.1.5 `set_probabilities(new_probs, by_rows = False)`

The method to set the probability values if the table type (`distr_type`) of a `Node` is "Manual". `new_probs` is a list of lists containing numerical values, and the length of the input list depends on the number of the states of the node and of its parents.

You can format the input list in two different orders. If the parameter `by_rows` is set to `True`, the method will read the input list to fill in the NPT row by row; if set to `False` (it is `False` by default), the method will read the input list to fill in the NPT column by columnn. This behaviour is illustrated with use case examples later in this document.

### 4.1.6 `set_expressions(new_expr, partition_parents = optional)`
The method to set the probability values if the table type (`distr_type`) of a `Node` is "Expression" or "Partitioned". If the table type is "Expression", `new_expr` is a list of size one and `partition_parents` is left untouched. If the table type is "Partitioned", `new_expr` is a list of expressions for each parent state, and `partition_parents` is a list of strings for each partitioned parent node's `id`. See the following sections for examples.

### 4.1.7 `set_variable(variable_name, variable_value)`

A method to set variables (constants) for a node. Takes the `variable_name` and `variable_value` inputs which define a new variable (constant) for the node.

### 4.1.8 `remove_variable(variable_name)`

A method to remove one of the existing variables (constants) from a node, using the `variable_name`.

## 4.2 `Network` methods

As described above, `Node` objects can be created and manipulated outside a network in the python environment. Once they are defined, they can be added to a `Network` object. Alternatively, a `Network` object can be created first and then its nodes can be specified. The python environment gives the user freedom, which is different from agena.ai Modeller where it is not possible to have a node completely outside any network. Once a `Network` object is created, with or without nodes, the following methods can be used to modify and manipulate the object.

### 4.2.1 `add_node(new_node)`

A method to add a new `Node` object to the `nodes` field of a `Network` object. The input `new_node` is a `Node` object and it is added to the network if it's not already in it.

Note that adding a new `Node` to the network does not automatically add its parents or children to the network. If the node has parents already defined, you need to add all the parent `Node`s separately to the network, too.

### 4.2.2 `remove_node(old_node)`

A method to remove an existing `Node` object from the network. Note that removing a Node from a network doesn't automatically remove it from its previous parent-child relationships in the network. You need to adjust such relationships separately on `Node` level.

### 4.2.3 `plot()`

A method to plot the graphical structure of a BN network.

## 4.3 `Model` methods

A `Model` object consists of networks, network links, datasets, and settings. A new `Model` object can be created with a network (or multiple networks). By default, it is created with a single empty dataset (scenario) called "Case 1". Following methods can be used to modify `Model` objects: 

### 4.3.1 `add_network(new_network)`

A method to add a new `Network` object to the `networks` field of a `Model` object. The input `new_network` is a `Network` object and it is added to the model if it's not already in it.

### 4.3.2 `remove_network(old_network)`

A method to remove an existing `Network` object from the model. Note that removing a Node from a network doesn't automatically remove its possible network links to other networks in the model. `network-links` field of a `Model` should be adjusted accordingly if needed.

### 4.3.4 `add_network_link(source_network, source_node, target_network, target_node, link_type, pass_state = optional)`

This is the method to add links to a model between its networks. These links start from a "source node" in a network and go to a "target node" in another network. To create the link, the source and target nodes in the networks need to be specified together with the network they belong to (by the `Node` and `Network` `id`s). The input parameters are as follows:

* `source_network` = `Network.id` of the network the source node belongs to
* `source_node` = `Node.id` of the source node
* `target_network` = `Network.id` of the network the target node belongs to
* `target_node` = `Node.id` of the target node
* `link_type` = a string of the link type name. If not specified, it is `Marginals`. It can be one of the following:
    * Marginals
    * Mean
    * Median
    * Variance
    * StandardDeviation
    * LowerPercentile
    * UpperPercentile
    * State
* `pass_state` = one of the `Node.states` of the source node. It has to be specified only if the `link_type` of the link is `"State"`, otherwise is left blank.

Note that links between networks are allowed only when the source and target nodes fit certain criteria. Network links are allowed if:

* Both nodes are the same type and either of them is simulated
* Both nodes are the same type and neither is simulated and both have the same number of states
* Source node is not numeric interval or discrete real and target node is simulated

### 4.3.5 `remove_network_link(source_network, source_node,target_network, target_node)`

A method to remove network links, given the `id`s of the source and target nodes (and the networks they belong to).

### 4.3.6 `remove_all_network_links()`

A method to remove all existing network links in a model.

### 4.3.7 `create_dataset(dataset_id)`

It is possible to add multiple cases to a model. These cases are new `Dataset` objects added to the `datasets` field of a model. Initially these cases have no observations and are only defined by their `id`s. The cases are populated with the `enter_observation()` function. The `create_dataset()` function takes the `id` of the new dataset to be added as input. 

### 4.3.8 `remove_dataset(dataset_id)`

A method to remove an existing scenario from the model. Input parameter `dataset_id` is the string which is the `id` of a dataset (case).

### 4.3.9 `enter_observation(network_id, node_id, value, dataset_id = optional, variable_input = False)`

A method to enter observation to a model. To enter the observation to a specific dataset (case), the dataset id must be given as the input parameter `dataset`. If `dataset` is left blank, the entered observation will by default go to the first dataset (case) of the model (called "Case 1" by default). This means that if there is no extra datasets created for a model (which by default comes with "Case 1"), any observation entered will be set for this dataset (mimicking the behaviour of entering observation to agena.ai Modeller).

The observation is defined with the mandatory input parameters:
* `network_id` = `Network.id` of the network the observed node belongs to
* `node_id` = `Node.id` of the observed node
* `value` = this parameter can be:
    * the value or state of the observation for the observed node (if it is hard evidence)
    * the id of a variable (constant) defined for the node (if `variable_input` is `True`)
    * the array of multiple values and their weights (if it is soft evidence)
* `variable_input` = a boolean parameter, set to `True` if the entered observation is a variable (constant) id for the node instead of an observed value.

### 4.3.10 `remove_observation(network_id, node_id, dataset_id = optional)`

A method to remove a specific observation from the model. It requires the id of the node which has the observation to be removed and the id of the network the node belongs to.

### 4.3.11 `clear_dataset_observations(dataset_id)`

A method to clear all observations in a specific dataset (case) in the model.

### 4.3.12 `clear_all_observations()`

A method to clear all observations defined in a model. This function removes all observations from all datasets (cases).

### 4.3.13 `import_results(results_file)`

[TO BE IMPLEMENTED]

### 4.3.14 `change_settings(setting arguments)`

A method to change model settings. The input parameters can be some or all of the `settings` fields. For example:

```python
example_model.change_settings(convergence=0.001, iterations=75)
```

### 4.3.15 `default_settings()`

A method to reset model settings back to default values. The default values for model settings are:

* discreteTails = False
* sampleSizeRanked = 5
* convergence = 0.01
* iterations = 50
* tolerance = 1

### 4.3.16 `save_to_file(filename)`

A method to export the `Model` to a .cmpx or a .json file. This method passes on all the information about the model, its datasets, its networks, their nodes, and model settings to a file in the correct format readable by agena.ai.

Input parameter `filename` must have a file extension of '.cmpx' or '.json'.

### 4.3.17 `get_results()`

A method to generate a .csv file based on the calculation results a Model contains. See [Section 8.2](#82-model-calculation) for details.

### 4.3.18 `from_cmpx(filepath = "/path/to/model/file.cmpx")`

This is the class method to create a `Model` object from a .cmpx file. The method parses the .cmpx file and creates the python objects based on the model in the file. To see its use, see examples below.

### 4.3.19 `create_batch_cases(input_data, update_model = True)`

A method to import a series of cases (datasets) and their observations from a .csv file. If the .csv file is prepared in the correct format (see examples below), the method will do either of the following:

* if `update_model` is `True` (default): it will create new datasets for each row in the csv file and enter all the non-missing observations in the row to the model. The model now contains new datasets (cases) with the observations.
* if `update_model` is `False`: it will create new datasets for each row in the csv file and enter all the non-missing observations in the row to the model, and export the model to a local .json file, and reset the python `Model` object. Now the model does not contain new datasets (cases) but there's a locally saved .json model with all the datasets and observations.

### 4.3.20 `create_csv_template()`

This method creates an empty CSV file with the correct format so that it can be filled in and used for `create_batch_bases()`. Note that this template includes every single node in the model, not all of which might be observable - you can delete the columns of the nodes which will not be observed.

### 4.3.21 `create_sensitivity_config(...)`

A method to create a sensitivity configuration object if a sensitivity analysis request will be sent to agena.ai Cloud servers or the local API. Its parameters are:

* `targetNode` = target node ID for the analysis
* `sensitivityNodes` = a list of sensitivity node IDs
* (optional) `network` = ID of the network to perform analysis on. If missing, the first network in the model is used
* (optional) `dataSet` = ID of the dataSet (scenario) to use for analysis
* (optional) `report_settings` = a dictionary for settings for the sensitivity analysis report. The elements of the dictionary are:
    * `"summaryStats"` (a list with some/all of the following fields)
        * mean
        * median
        * variance
        * standardDeviation
        * upperPercentile
        * lowerPercentile
    * `"sumsLowerPercentileValue"` (set the reported lower percentile value.
Default is 25)
    * `"sumsUpperPercentileValue"` (set the reported upper percentile value.
Default is 75)
    * `"sensLowerPercentileValue"` (lower percentile value to limit sensitivity node data by. Default is 0)
    * `"sensUpperPercentileValue"` (upper percentile value to limit sensitivity node data by. Default is 100)

For the use of the function, see Sections [8](#8-agenaai-cloud-with-pyagena) and [9](#9-local-agenaai-api-with-pyagena).

## 4.5 agena.ai Cloud Related Functions

pyagena allows users to send their models to agena.ai Cloud servers for calculation. The functions around the server capabilities (including authentication) are described in [Section 8](#8-agenaai-cloud-with-pyagena).

## 4.6 agena.ai Local API Related Functions

pyagena allows users to connect to the local agena.ai developer API for calculation. The functions about the local developer API communication are descibed in [Section 9](#9-local-agenaai-api-with-pyagena).

# 5. Importing a Model from .cmpx

To import an existing agena.ai model (from a .cmpx file), create a new `Model` object using the `from_cmpx()` option:

```python
new_model = Model.from_cmpx("/path/to/model/file.cmpx")
```

This creates a python `Model` object with all the information taken from the .cmpx file. All fields and sub-fields of the `Model` object are accessible now. For example, you can see the networks in this model with:

```python
new_model.networks
```

Each network in the model is a `Network` object, therefore you can access its fields with the same logic, for example to see the id of the first network and all the nodes in the first network in the BN, use respectively:

```python
new_model.networks[0].id
```

```python
new_model.networks[0].nodes
```

Similarly, each node in a network itself is a `Node` object. You can display all the fields of a node. Example uses for the second node in the first network of a model:

```python
new_model.networks[0].nodes[0].id
```

```python
new_model.networks[0].nodes[1].states
```

Once the python model is created from the imported .cmpx file, the `Model` object as well as all of its `Network`, `Dataset`, and `Node` objects can be manipulated using python methods.

# 6. Creating and Modifying a Model in python

It is possible to create an agena.ai model entirely in python, without a .cmpx file to begin with. Once all the networks and nodes of a model are created and defined in python, you can export the model to a .cmpx or .json file to be used with agena.ai calculations and inference, locally or on agena.ai Cloud. In this section, creating a model is shown step by step, starting with nodes.

## 6.1 Creating Nodes

In the python environment, `Node` objects represent the nodes in BNs, and you can create `Node` objects before creating and defining any network. To create a new node, only its id (unique identifier) is mandatory, you can define some other optional fields upon creation if desired. A new node creation function takes the following parameters where id is the only mandatory one and all others are optional:

```python
Node(id, name, description, type, simulated, states)

# id parameter is mandatory
# the rest is optional
```

If the optional fields are not specified, the nodes will be created with the defaults. The default values for the fields, if they are not specified, are:

* name = node id
* description = "New Node"
* simulated = False
* type = 
    * if simulated: "ContinuousInterval"
    * if not simulated: "Boolean"
* states =
    * if Boolean or Labelled: ["False", "True"]
    * if Ranked: ["Low", "Medium", "High"]
    * if DiscreteReal: ["0.0", "1.0"]

Once a new node is created, depending on the type and number of states, other fields are given sensible default values too. These fields are distr_type (table type), probabilities or expressions. To specify values in these fields, you need to use the relevant set functions (explained above and shown later in this section). The default values for these fields are:

* distr_type = 
    * if simulated: "Expression"
    * if not simulated: "Manual"
* probabilities = 
    * if distr_type is Manual: discrete uniform distribution, each state has the probability of (1/number of states)
* expressions = 
    * if distr_type is Expression: "Normal(0,1000000)"

Look at the following new node creation examples:

```python
node_one = Node(id = "node_one")
```

```python
node_two = Node(id = "node_two", name = "Second Node")
```

```python
node_three = Node(id = "node_three", type = "Ranked")
```

```python
node_four = Node(id = "node_four", type = "Ranked", states = ["Very low", "Low", "Medium", "High", "Very high"])
```

Looking up some example values in the fields that define these nodes:

* node_one.id = "node_one"
* node_one.name = "node_one"
* node_one.description = "New Node"
* node_one.type = "Boolean"
* node_one.states = ["False", "True"]
* node_two.id = "node_two"
* node_two.name = "Second Node"
* node_three.type = "Ranked"
* node_three.states =  ["Low", "Medium", "High"]
* node_four.states =  ["Very low", "Low", "Medium", "High", "Very high"]
* node_one.distr_type = "Manual"
* node_one.probabilities = [[0.5, 0.5]]
* node_three.probabilities = [[0.3333, 0.3333, 0.3333]]
* node_four.probabilities = [[0.2, 0.2, 0.2, 0.2, 0.2]]

Note that probabilities will be a list (of size one) of lists even when there is no parent node.

## 6.2 Modifying Nodes

To update node information, some fields can be simply overwritten with direct access to the field if it does not affect other fields. These fields are node name and description.

```python
node_one.description = "first node we have created"
```

Other fields can be specified with the relevant set functions. To update the node states, you can use `set_states()`:

```python
node_one.set_states(["Negative","Positive"])
```

Note that the input for `set_states()` is a list of node names. If this method changes the number of node states, the NPT will be adjusted accordingly and state probabilities will reset to uniform.

To set probability values for a node with a manual table (distr_type), you can use `set_probabilities()` function:

```python
node_one.set_probabilities([[0.2,0.8]])
```

Note that the `set_probabilities()` function takes a list of lists as input, even when the node has no parents and its NPT has only one row of probabilities. If the node has parents, the NPT will have multiple rows which should be in the input list.

Assume that `node_one` and `node_two` are the parents of `node_three` (how to add parent nodes is illustrated later in this section). Now assume that you want `node_three` to have the following NPT:

<table>
<tbody>
  <tr>
    <td><strong>node_one</strong></td>
    <td colspan="2"><strong>Negative</strong></td>
    <td colspan="2"><strong>Positive</strong></td>
  </tr>
  <tr>
    <td><strong>node_two</strong></td>
    <td><strong>False</strong></td>
    <td><strong>True</strong></td>
    <td><strong>False</strong></td>
    <td><strong>True</strong></td>
  </tr>
  <tr>
    <td>Low</td>
    <td>0.1</td>
    <td>0.2</td>
    <td>0.3</td>
    <td>0.4</td>
  </tr>
  <tr>
    <td>Medium</td>
    <td>0.4</td>
    <td>0.45</td>
    <td>0.6</td>
    <td>0.55</td>
  </tr>
  <tr>
    <td>High</td>
    <td>0.5</td>
    <td>0.35</td>
    <td>0.1</td>
    <td>0.05</td>
  </tr>
</tbody>
</table>

There are two ways to order the values in this table for the `set_probabilities()` function, using the boolean `by_rows` parameter. If you want to enter the values following the rows in agena.ai Modeller NPT rather than ordering them by the combination of parent states (columns), you can use `by_rows = True` where each element of the list is a row of the agena.ai Modeller NPT:

```python
node_three.set_probabilities([[0.1, 0.2, 0.3, 0.4], [0.4, 0.45, 0.6, 0.55], [0.5, 0.35, 0.1, 0.05]]), by_rows = True)
```

If, instead, you want to define the NPT with the probabilities that add up to 1 (conditioned on the each possible combination of parent states), you can set `by_rows = False` as the following example:

```python
node_three.set_probabilities([[0.1, 0.4, 0.5], [0.2, 0.45, 0.35], [0.3, 0.6, 0.1], [0.4, 0.55, 0.05]]), by_rows = False)
```

Similarly, you can use `set_expressions()` function to define and update expressions for the nodes without Manual NPT tables. If the node has no parents, you can add a single expression:

```python
example_node.set_expressions(["TNormal(4,1,-10,10)"])
```

Or if the node has parents and the expression is partitioned on the parents:

```python
example_node.set_expressions(["Normal(90,10)", "Normal(110,15)", "Normal(120,30)"], partition_parents = ["parent_node"])
```

In the former example the expression is a list of size one, and in the latter the expression is a list with three elements and the second parameter (`partition_parameters`) is a list which contains the ids of the parent nodes. In the second example, expression input has three elements based on the number of states of the parent node(s) on which the expression is partitioned.

## 6.3 Adding and Removing Parent Nodes

To add parents to a node, you can use `add_parent()` function. For example:

```python
node_three.add_parent(node_one)
```

This adds `node_one` to the parents list of `node_three`, and resizes the NPT of `node_three` (and resets the values to a discrete uniform distribution).

To remove an already existing parent, you can use:

```python
node_three.remove_parent(node_one)
```

This removes `node_one` from the parents list of `node_three`, and resizes the NPT of `node_three` (and resets the values to a discrete uniform distribution).

Below we follow the steps from creation of node_three to the parent modifications and see how the NPT of node_three changes after each step.

* Creating node_tree with only type specified:

```python
node_three = Node(id = "node_three", type = "Ranked")
```
* `node_three.parents`:

```python
[]
```

* `node_three.probabilities`:

```python
[[0.3333333333333333, 0.3333333333333333, 0.3333333333333333]]

#discrete uniform with three states (default of Ranked node)
```

* Changing the probabilities:

```python
node_three.set_probabilities([[0.7, 0.2, 0.1]])
```

* `node_three.probabilities`:

```python
[[0.7, 0.2, 0.1]]
```

* Adding a parent:

```python
node_three.add_parent(node_one)
```

* `node_three.parents`:

```python
[Node: node_one (Boolean)]

# node_one has been added to the parents list of node_three
```

* `node_three.probabilities`:

```python
[[0.3333333333333333, 0.3333333333333333, 0.3333333333333333],
 [0.3333333333333333, 0.3333333333333333, 0.3333333333333333]]

#  NPT of node_three has been resized based on the number of parent node_one states
# NPT values for node_three are reset to discrete uniform
```

* Adding another parent:

```python
node_three.add_parent(node_two)
```

* `node_three.parents`:

```python
[Node: node_one (Boolean), Node: node_two (Boolean)]

# node_two has been added to the parents list of node_three
```

* `node_three.probabilities`:

```python
[[0.3333333333333333, 0.3333333333333333, 0.3333333333333333],
 [0.3333333333333333, 0.3333333333333333, 0.3333333333333333],
 [0.3333333333333333, 0.3333333333333333, 0.3333333333333333],
 [0.3333333333333333, 0.3333333333333333, 0.3333333333333333]]

#  NPT of node_three has been resized based on the number of parent node_one and node_two states
# NPT values for node_three are reset to discrete uniform
```

## 6.4 Creating and Modifying Networks

BN Models contain networks, at least one or optionally multiple. If there are multiple networks in a model, they can be linked to each other with the use of input and output nodes. A `Network` object in python represents a network in a BN model. To create a new `Network` object, you need to specify its id (mandatory parameter), and you can also fill in the optional parameters:

```python
Network(id, name, description, nodes)

# id parameter is mandatory
# the rest is optional
```

Here clearly `nodes` field is the most important information for a network but you do not need to specify these on creation. You can choose to create an empty network and fill it in with the nodes afterwards with the use of `add_node()` function. Alternatively, if all (or some) of the nodes you will have in the network are already defined, you can pass them to the new `Network` object on creation.

Below is an example of network creation with the nodes added later:

```python
network_one = Network(id = "network_one")

network_one.add_node(node_three)
network_one.add_node(node_one)
network_one.add_node(node_two)
```

Notice that when node_three is added to the network, its parents are not automatically included. So if a node has parents, you need to separately add them to the network, so that later on your model will not have discrepancies.

The order in which nodes are added to a network is not important as long as all parent-child nodes are eventually in the network.

Alternatively, you can create a new network with its nodes:

```python
network_two = Network(id = "network_two", nodes = [node_one, node_two, node_three])
```

Or you can create the network with some nodes and add more nodes later on:

```python
network_three = Network(id = "network_three", nodes = [node_one, node_three])

network_three.add_node(node_two)
```

To remove a node from a network, you can use `remove_node()` function. Again keep in mind that removing a node does not automatically remove all of its parents from the network. For example,

```python
network_three.remove_node(node_three)
```

## 6.5 Creating and Modifying the Model

BN models consist of networks, the links between networks, and datasets (scenarios). Only the networks information is mandatory to create a new `Model` object in python. The other fields can be filled in afterwards. The new model creation function is:

```python
Model(id, networks, dataSets, networkLinks)

# networks parameter is mandatory
# the rest is optional
```

For example, you can create a model with the networks defined above:

```python
example_model = Model(networks = [network_one])
```

Note that even when there is only one network in the model, the input has to be a list. Networks in a model can be modified with `add_network()` and `remove_network()` functions:

```python
example_model.add_network(network_two)
```

```python
example_model.remove_network(network_two)
```

Network links between networks of the model can be added with the `add_network_link()` function. For example:

```python
example_model.add_network_link(source_network = network_one, source_node = node_three, target_network = network_two, target_node = node_three, link_type = "Marginals")
```

For link_type options and allowed network link rules, see `add_network_link()` in the previous section.

When a new model is created, it comes with a single dataset (case) by default. See next section to see how to add observations to this dataset (case) or add new datasets (cases).

## 6.6 Creating Datasets (Cases) and Entering Observation

To enter observations to a Model (which by default has one single case), use the `enter_observation()` function. You need to specify the node (and the network it belongs to) and give the value (one of the states if it's a discrete node, a sensible numerical value if it's a continuous node):

```python
example_model.enter_observation(node_id = node_three, network_id = network_one, value = "High")
```

Note that this function did not specify any dataset (case). If this is the case, observation is always entered to the first (default) case.

You may choose to add more datasets (cases) to the model with the `create_dataset()` function:

```python
example_model.create_dataset("Case 2")
```

Once added, you can enter observation to the new dataset (case) if you specify the `dataset` parameter in the `enter_observation()` function:

```python
example_model.enter_observation(dataset_id = "Case 2", node_id = node_three, network_id = network_one, value = "Medium")
```

## 6.7. Exporting a Model to .cmpx or .json

Once a python model is defined fully and it is ready for calculations, you can export it to a .cmpx or a .json file:

```python
example_model.save_to_file("example_model.cmpx")
```

or

```python
example_model.save_to_file("example_model.json")
```


# 7. Creating Batch Cases for a Model in python

pyagena allows creation of batch cases based on a single model and multiple observation sets. Observations should be provided in a CSV file with the correct format for the model. In this CSV file, each row of the data is a single case (dataset) with a set of observed values for nodes in the model. First column of the CSV file is the dataset (case) ids which will be used to create a new dataset for each data row. All other columns are possible evidence variables whose headers follow the "network_id.node_id" format. Thus, each column represents a node in the BN and is defined by the node id and the id of the network to which it belongs. The column header for the first one (dataset names) can be anything, 'Case' is the header name when `create_csv_template()` is used.

An example CSV format is as below:

<table>
<thead>
  <tr>
    <th>Case</th>
    <th>network_one.node_one</th>
    <th>network_one.node_two</th>
    <th>network_one.cont_node</th>
    <th>network_two.node_one</th>
    <th>network_two.node_two</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>Case 1</td>
    <td>Negative</td>
    <td>True</td>
    <td>20</td>
    <td>Negative</td>
    <td>False<br></td>
  </tr>
  <tr>
    <td>Case 2</td>
    <td>Positive<br></td>
    <td>True</td>
    <td></td>
    <td>Negative</td>
    <td>True</td>
  </tr>
  <tr>
    <td>New Case</td>
    <td>Positive</td>
    <td>False</td>
    <td>18</td>
    <td>Positive</td>
    <td></td>
  </tr>
</tbody>
</table>

Once the model is defined in pyagena and the CSV file with the observations is prepared, you can use `create_batch_cases()` to generate scenarios for the BN, either to update the `Model` object or to save the model with observations locally and not change the `Model` object:

```python
example_model.create_batch_cases("example_dataset.csv", update_model = True)
```

This will create new datasets (cases) for each row of the dataset in the model, fill these datasets (cases) in with the observations using the values given in the dataset. If `update_model` is `True`, the python model will keep the new cases and observations. If `False`, the method will create a new .json file for the model with all the datasets (cases), save locally, and remove the newly added cases from the model. The `update_model` parameter is `True` by default, unless specified otherwise. Missing values must be blank cells in the dataset. If there are missing values in the dataset, it will not fill in any observation for that specific node in that specific dataset (case).

You can use `create_csv_template()` function on a Model object to create an empty .csv file with the correct format for all the nodes and networks in the model. You can then delete the columns for the nodes that are not observed.

# 8. agena.ai Cloud with pyagena

Once the Bayesian network model is prepared and modified and is ready for calculations, you can connect to either agena.ai Cloud or a local agena.ai developer API environment for calculations.

pyagena allows you to authenticate with agena.ai Cloud (using your existing account) and send your model files to Cloud for calculations. The connection between your local python environment and agena.ai Cloud servers is based on the python `requests` package.


## 8.1 Authentication

The cloud operations use a python object called `login` to authenticate the user account, and allows user to run further calculations.

To create an account, visit https://portal.agena.ai. Once created, you can use your credentials in pyagena to access the servers.

```python
example_user = login()
```

If you give no parameters, you will be prompted to enter your username and password for authentication. Alternatively you can pass them as parameters to login constructor:

```python
example_user = login(username, password)
```

This will send a POST request to authentication server, and will create a logged in user instance (including access and refresh tokens) which will be used to authenticate further operations.

You can choose to see either basic operation result messages or detailed debugging messages when you use the model calculation and sensitivity analysis functions after authentication. You can set the debug message option for the logged in cloud user with:

```python
example_user.set_debug(True)
```


## 8.2 Model Calculation

Using the login instance created, you can do further operations such as calculations and sensitivity analysis.

`calculate()` function is used to send a python model object to agena.ai Cloud servers for calculation. This is a method of the logged in user instance. The function takes the following parameters:

* `model` is the python Model object
* (optional) `dataset` is the id of the dataset that contains the set of observations (`.id` of one of the `.datasets` objects) if any. If the model has only one dataset (case) with observations, dataset needs not be specified (it is also possible to send a model without any observations).

Currently servers accept a single set of observations for each calculation, if the python model has multiple datasets (cases), you need to specify which dataset is to be used.

For example,

```python
example_user.calculate(example_model)
```

or

```python
example_user.calculate(example_model, dataset_id)
```

If the calculation is successful, this function will update the python model (the relevant `.results` field in the model's `.dataset`) with results of the calculation obtained from agena.ai Cloud.

The model calculation computation supports asynchronous request (polling) if the computation job takes longer than 10 seconds. The python client will periodically recheck the servers and obtain the results once the computation is finished (or timed out, whichever comes first).

If you would like to see the calculation results in a .csv format, you can use the Model method `get_results()` to generate the output file.

```python
example_model.get_results()
```

or with a custom file name:

```python
example_model.get_results("example_output_file")
```

This will generate a .csv file with the following format:

<table>
<thead>
  <tr>
    <th>Case</th>
    <th>Network</th>
    <th>Node</th>
    <th>State</th>
    <th>Probability</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>Case 1</td>
    <td>Network 1</td>
    <td>Node 1</td>
    <td>State 1</td>
    <td>0.2</td>
  </tr>
  <tr>
    <td>Case 1</td>
    <td>Network 1</td>
    <td>Node 1</td>
    <td>State 2</td>
    <td>0.3</td>
  </tr>
  <tr>
    <td>Case 1</td>
    <td>Network 1</td>
    <td>Node 1</td>
    <td>State 3</td>
    <td>0.5</td>
  </tr>
  <tr>
    <td>Case 1</td>
    <td>Network 1</td>
    <td>Node 2</td>
    <td>State 1</td>
    <td>0.3</td>
  </tr>
  <tr>
    <td>Case 1</td>
    <td>Network 1</td>
    <td>Node 2</td>
    <td>State 2</td>
    <td>0.7</td>
  </tr>
  <tr>
    <td>Case 1</td>
    <td>Network 1</td>
    <td>Node 3</td>
    <td>State 1</td>
    <td>0.1</td>
  </tr>
  <tr>
    <td>Case 1</td>
    <td>Network 1</td>
    <td>Node 3</td>
    <td>State 2</td>
    <td>0.8</td>
  </tr>
  <tr>
    <td>Case 1</td>
    <td>Network 1</td>
    <td>Node 3</td>
    <td>State 3</td>
    <td>0.1</td>
  </tr>
</tbody>
</table>


## 8.3 Sensitivity Analysis

Sensitivity analysis is another cloud server operation for the logged in user instance. For the sensitivity analysis, first you need to crate a sensivity configuration object, using the `.create_sensitivity_config(...)` method of a Model. For example,

```python
example_sens_config = example_model.create_sensitivity_config(
                      targetNode = "node_one",
                      sensitivityNodes = ["node_two","node_three"],
                      report_settings = {"summaryStats" : ["mean", "variance"]},
                      dataSet = "dataset_id",
                      network = "network_one")
```

Here, `targetNode` and `sensitivityNodes` parameters are mandatory for a sensitivity configuration and the rest is optional with sensible defaults assigned on the cloud servers.

Using the defined configuration object, now you can use the `sensitivity_analysis()` method of the logged in user instance to send the request to the server. For example,

```python
sa_results = example_user.sensitivity_analysis(example_model, example_sens_config)
```

If successful, this will return a `dict` with some information about the process and the results. Unlike `calculate()`, this method is advised to assign to a variable for future analysis and use. The returned `dict` includes the following fields:

* lastUpdated
* version
* log
* uuid
* debug
* duration
* messages
* results
* memory

The results contains raw results data for all analysis report options defined, such as tables, tornado graphs, and curve graphs. To access the results:

```python
sa_results["results"]
```

You can see the cloud API documentation for further information on the sensitivity analysis response [here (Manual/Tools: Sensitivity Analysis/Response)](https://agenarisk.atlassian.net/wiki/spaces/PROTO/pages/785711115/agena.ai+cloud+api+manual#agena.aicloudapimanual-Response.3).

The sensitivity analysis computation supports asynchronous request (polling) if the computation job takes longer than 10 seconds. The python client will periodically recheck the servers and obtain the results once the computation is finished (or timed out, whichever comes first).

# 9. Local agena.ai API with pyagena

Agena.ai has a [Java based API](https://github.com/AgenaRisk/api) to be used with agena.ai developer license. If you have the developer license, you can use the local API for calculations in addition to agena.ai modeller or cloud. The local API has Java and maven dependencies, which you can see on its github page in full detail. pyagena allows communications with the local agena developer API.

## 9.1 Setting up the local API directory

To manually set up the local agena developer API, follow the instructions on the github page for the API: https://github.com/AgenaRisk/api.

Or, for the API setup you can use the python environment:

```python
local_api_clone()
```

to clone the git repository of the API in your working directory.

Once the API is cloned, you can compile maven environment with:

```python
local_api_compile()
```

Note that for this to work you need to stay in your current working directory, you don't need to navigate into the cloned api folder. The python function will compile the api directory as long as it's a sub-directory of the current working directory (default behaviour if `local_api_clone()` is used to clone the repository.)

And if needed, activate your agena.ai developer license with

```python
local_api_activate_license("1234-ABCD-5678-EFGH")
```

passing on your developer license key as the input parameter.

**!! Note that when there is a new version of the agena developer API, you need to re-run `local_api_compile()` function to update the local repository.**

## 9.2 Model calculation with the local API

Once the local API is compiled and developer license is activated, you can use the local API directly with your models defined in python. To use the local API for calculations of a model created in python:

```python
local_api_calculate(model, dataset_id)
```

where the parameter `model` is a python Model object and `dataset_id` is the id of one of the datasets (cases) existing in the Model object. For example,

```python
local_api_calculate(model = example_model,
                    dataset_id = "example_dataset_id")
```

This function will temporarily create the .cmpx file for the model and the separate .json file required for the dataset, and send them to the local API (cloned and compiled within the working directory), obtain the calculation result values and update the python Model object with the calculation results.

If you'd like to run multiple datasets in the same model in batch, you can use `local_api_batch_calculate()` instead. This function takes a python Model object as input and runs the calculation for each dataset in it, and fills in all the relevant result fields under each dataset. You can use this function as

```python
local_api_batch_calculate(model = example_model)
```

where `example_model` is a python Model object with multiple dataSets.

If you would like to see the calculation results in a .csv format, you can use the Model method `get_results()` to generate the output file as described in [Section 8.2](#82-model-calculation).


## 9.3 Sensitivity Analysis with the local API

You can also run a sensitivity analysis in the local API, using

```python
local_api_sensitivity_analysis(model, sens_config)
```

Here the sens_config is created by the use of `.create_sensitivity_config(...)` method of a Model. For example: 

```python
example_sens_config = example_model.create_sensitivity_config(
                      targetNode = "node_one",
                      sensitivityNodes = ["node_two","node_three"],
                      report_settings = {"summaryStats" : ["mean", "variance"]},
                      dataSet = "dataset_id",
                      network = "network_one")
```

Note that, unlike `local_api_calculate()`, this function does not update the existing Model object but returns a new `dict` of results. So it's a good practice to assign the function to a variable for future analysis and use.

```python
sa_results = local_api_sensitivity_analysis(model = example_model,
                      sens_config = example_sens_config)
```

This function will temporarily create the .cmpx file for the model and the separate .json files required for the dataset and sensitivity analysis configuration file, and send them to the local API (cloned and compiled within the working directory), obtain the sensitivity analysis result values and create the results `dict`. The returned `dict` includes the result values for displays such as sensitivity tables, tornado graphs, and curves. `local_api_sensitivity_analysis()` looks at the `dataSet` field of `sens_config` to determine which dataset to use, if the field doesn't exist, the default behaviour is to create a new dataset without any observations for the sensitivity analysis.

# 10. pyagena Use Case Examples

In this section, some use case examples of pyagena environment are shown. 

## 10.1 Diet Experiment Model

This is a BN which uses experiment observations to estimate the parameters of a distribution. In the model structure, there are nodes for the parameters which are the underlying parameters for all the experiments and the observed values inform us about the values for these parameters. The model in agena.ai Modeller is given below:

![Diet Experiment Image](https://resources.agena.ai/materials/repos/r_diet_image.png)

In this section we will create this model entirely in RAgena environment. We can start with creating first four nodes. 

Mean and variance nodes:

```python
from node import Node
from network import Network
from dataset import Dataset
from model import Model

#First we create the "mean" and "variance" nodes

mean = Node(id="mean", simulated=True)
mean.set_expressions(["Normal(0.0,100000.0)"])

variance = Node(id="variance", simulated=True)
variance.set_expressions(["Uniform(0.0,50.0)"])
```

Common variance and tau nodes:

```python
#Now we create the "common variance" and its "tau" parameter nodes

tau = Node(id="tau", simulated=True)
tau.set_expressions(["Gamma(0.001,1000.0)"])

common_var = Node(id="common_var", name="common variance", simulated=True)
common_var.add_parent(tau)
common_var.set_expressions(["Arithmetic(1.0/tau)"])
```

Now we can create the four mean nodes, using a for loop and list of `Node`s:

```python
#Creating a list of four mean nodes, "mean A", "mean B", "mean C", and "mean D"

mean_names = ["A", "B", "C", "D"]
means_list = []

for mn in mean_names:
    this_mean = Node(id="mean" + mn, name="mean " + mn)
    this_mean.add_parent(mean)
    this_mean.add_parent(variance)
    this_mean.set_expressions(["Normal(mean,variance)"])
    means_list.append(this_mean)
```

Now we can create the experiment nodes, based on the number of observations which will be entered:

```python
# Defining the list of observations for the experiment nodes
# and creating the experiment nodes y11, y12, ..., y47, y48

observations = [[62, 60, 63, 59],
                [63, 67, 71, 64, 65, 66],
                [68, 66, 71, 67, 68, 68],
                [56, 62, 60, 61, 63, 64, 63, 59]]

obs_nodes_list = []

for i, (obs, mn) in enumerate(zip(observations, means_list)):
    for j, ob in enumerate(obs):
        this_obs = Node(id="y"+str(i)+str(j), simulated=True)
        this_obs.add_parent(common_var)
        this_obs.add_parent(mn)
        this_obs.set_expressions(["Normal("+mn.id+",common_var)"])
        obs_nodes_list.append(this_obs)
```

We can create a network for all the nodes:

```python
# Creating the network for all the nodes

diet_network = Network(id = "Hierarchical_Normal_Model_1",
                       name = "Hierarchical Normal Model")
```

And add all the nodes to this network:

```python
# Adding all the nodes to the network

for nd in [mean, variance, tau, common_var, *means_list, *obs_nodes_list]:
    diet_network.add_node(nd)
```

Now we can create a model with this network:

```python
# Creating a model with the network

diet_model = Model(id="Diet_Experiment_Model", networks=[diet_network])
```

We enter all the observation values to the nodes:

```python
# Entering all the observations

for i, obs in enumerate(observations):
    for j, ob in enumerate(obs):
        this_node_id = "y" + str(i) + str(j)
        diet_model.enter_observation(node_id=this_node_id,
                                     network_id=diet_model.networks[0].id,
                                     value=ob)
```

Now the model is ready with all the information, we can export it to either a .json or a .cmpx file for agena.ai Modeller calculations, send it to agena.ai Cloud or to local agena.ai developer API.

```python
# To create a local .cmpx file
diet_model.save_to_file("./diet_model_example.cmpx")

# Or sending it to local agena.ai developer API for calculation
local_api_calculate(diet_model, "Case 1")

# Or sending it to agena.ai Cloud for calculation
user = login()
user.calculate(diet_model, "Case 1")
```
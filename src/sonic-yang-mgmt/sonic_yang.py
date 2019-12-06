import yang as ly
import sys
import json
import glob

"""
Yang schema and data tree python APIs based on libyang python
"""
class sonic_yang:
    def __init__(self, yang_dir):
        self.yang_dir = yang_dir
        self.ctx = None
        self.module = None
        self.root = None

        try:
            self.ctx = ly.Context(yang_dir)
        except Exception as e:
	    self.fail(e)

    def fail(self, e):
	print(e)
	raise e

    """
    load_schema_module(): load a Yang model file
    input:    yang_file - full path of a Yang model file
    returns:  Exception if error
    """
    def load_schema_module(self, yang_file):
        try:
            self.ctx.parse_module_path(yang_file, ly.LYS_IN_YANG)
        except Exception as e:
            print("Failed to load yang module file: " + yang_file)
	    self.fail(e)

    """
    load_schema_module_list(): load all Yang model files in the list
    input:    yang_files - a list of Yang model file full path
    returns:  Exception if error
    """
    def load_schema_module_list(self, yang_files):
        for file in yang_files:
             try:
                 self.load_schema_module(file)
             except Exception as e:
                 self.fail(e)

    """
    load_schema_modules(): load all Yang model files in the directory
    input:    yang_dir - the directory of the yang model files to be loaded
    returns:  Exception if error
    """
    def load_schema_modules(self, yang_dir):
        py = glob.glob(yang_dir+"/*.yang")
        for file in py:
            try:
                self.load_schema_module(file)
            except Exception as e:
                self.fail(e)

    """
    load_schema_modules_ctx(): load all Yang model files in the directory to context: ctx
    input:    yang_dir,  context
    returns:  Exception if error, returrns context object if no error
    """
    def load_schema_modules_ctx(self, yang_dir=None):
        if not yang_dir:
            yang_dir = self.yang_dir

        ctx = ly.Context(yang_dir)

        py = glob.glob(yang_dir+"/*.yang")
        for file in py:
            try:
                ctx.parse_module_path(str(file), ly.LYS_IN_YANG)
            except Exception as e:
                print("Failed to parse yang module file: " + file)
                self.fail(e)

        return ctx

    """
    load_data_file(): load a Yang data json file
    input:    data_file - the full path of the yang json data file to be loaded
    returns:  Exception if error
    """
    def load_data_file(self, data_file):
       try:
           node = self.ctx.parse_data_path(data_file, ly.LYD_JSON, ly.LYD_OPT_CONFIG | ly.LYD_OPT_STRICT)
       except Exception as e:
           print("Failed to load data file: " + str(data_file))
           self.fail(e)
       else:
           self.root = node

    """
    get module name from xpath
    input:    path
    returns:  module name
    """
    def get_module_name(self, schema_xpath):
        module_name = schema_xpath.split(':')[0].strip('/')
        return module_name

    """
    get_module(): get module object from Yang module name
    input:   yang module name
    returns: Schema_Node object
    """
    def get_module(self, module_name):
        mod = self.ctx.get_module(module_name)
        return mod

    """
    load_data_model(): load both Yang module fileis and data json files
    input:   yang directory, list of yang files and list of data files (full path)
    returns: returns (context, root) if no error,  or Exception if failed
    """
    def load_data_model (self, yang_dir, yang_files, data_files, output=None):
        if (self.ctx is None):
            self.ctx = ly.Context(yang_dir)

        try:
            self.load_schema_module_list(yang_files)
            if len(data_files) == 0:
                return (self.ctx, self.root)

            self.load_data_file(data_files[0])

            for i in range(2, len(data_files)):
                self.merge_data(data_files[i])
        except Exception as e:
            print("Failed to load data files")
            self.fail(e)
            return

        if output is not None:
            self.print_data_mem(output)

        return (self.ctx, self.root)

    """
    print_data_mem():  print the data tree
    input:  option:  "JSON" or "XML"
    """
    def print_data_mem (self, option):
        if (option == "JSON"):
            mem = self.root.print_mem(ly.LYD_JSON, ly.LYP_WITHSIBLINGS | ly.LYP_FORMAT)
        else:
            mem = self.root.print_mem(ly.LYD_XML, ly.LYP_WITHSIBLINGS | ly.LYP_FORMAT)

        print("======================= print data =================")
        print(mem)

    """
    save_data_file_json(): save the data tree in memory into json file
    input: outfile - full path of the file to save the data tree to
    """
    def save_data_file_json(self, outfile):
        mem = self.root.print_mem(ly.LYD_JSON, ly.LYP_FORMAT)
        with open(outfile, 'w') as out:
            json.dump(mem, out, indent=4)

    """
    get_module_tree(): get yang module tree in JSON or XMAL format
    input:   module name
    returns: JSON or XML format of the input yang module schema tree
    """
    def get_module_tree(self, module_name, format):
        result = None

        try:
            module = self.ctx.get_module(str(module_name))
        except Exception as e:
            print("Cound not get module: " + str(module_name))
            self.fail(e)
        else:
            if (module is not None):
                if (format == "XML"):
                    #libyang bug with format
                    result = module.print_mem(ly.LYD_JSON, ly.LYP_FORMAT)
                else:
                    result = module.print_mem(ly.LYD_XML, ly.LYP_FORMAT)

        return result

    """
    validate_data(): validate data tree
    input:
           node:   root of the data tree
           ctx:    context
    returns:  Exception if failed
    """
    def validate_data (self, node=None, ctx=None):
        if not node:
            node = self.root

        if not ctx:
            ctx = self.ctx

        try:
            rc = node.validate(ly.LYD_OPT_CONFIG, ctx)
        except Exception as e:
            self.fail(e)

    """
    validate_data_tree(): validate the data tree
    returns: Exception if failed
    """
    def validate_data_tree (self):
        try:
            self.validate_data(self.root, self.ctx)
        except Exception as e:
            print("Failed to validate data tree")
            self.fail(e)

    """
    find_parent_node():  find the parent node object
    input:    data_xpath - xpath of the data node
    returns:  parent node
    """
    def find_parent_node (self, data_xpath):
        if (self.root is None):
            print("data not loaded")
            return None
        try:
            node = self.find_data_node(data_xpath)
        except Exception as e:
            print("Failed to find data node from xpath: " + str(data_xpath))
            self.fail(e)
        else:
            if node is not None:
                return node.parent()

        return None

    """
    get_parent_xpath():  find the parent node xpath
    input:    data_xpath - xpathof the data node
    returns:  - xpath of parent node
              - Exception if error
    """
    def get_parent_xpath (self, data_xpath):
        path=""
        try:
            node = self.find_parent_node(data_xpath)
        except Exception as e:
            print("Failed to find parent node from xpath: " + str(data_xpath))
            self.fail(e)
        else:
            if (node is not None):
                path = node.path()
        return path

    """
    new_node(): create a new data node in the data tree
    input:
           xpath: xpath of the new node
           value: value of the new node
    returns:  new Data_Node object if success,  Exception if falied
    """
    def new_node(self, xpath, value):
        val = str(value)
        try:
            node = self.root.new_path(self.ctx, xpath, val, 0, 0)
        except Exception as e:
            print("Failed to add data node for path: " + str(xpath))
            self.fail(e)
        else:
            return node

    """
    find_data_node():  find the data node from xpath
    input:    data_xpath: xpath of the data node
    returns   - Data_Node object if found
              - None if not exist
              - Exception if there is error
    """
    def find_data_node(self, data_xpath):
        try:
            set = self.root.find_path(data_xpath)
        except Exception as e:
            print("Failed to find data node from xpath: " + str(data_xpath))
            self.fail(e)
        else:
            if set is not None:
                for node in set.data():
                    if (data_xpath == node.path()):
                        return node
            return None
    """
    find_schema_node(): find the schema node from schema xpath
        example schema xpath:
        "/sonic-port:sonic-port/sonic-port:PORT/sonic-port:PORT_LIST/sonic-port:port_name"
    input:    xpath of the node
    returns:  Schema_Node oject or None if not found
    """
    def find_schema_node(self, schema_xpath):
        try:
            schema_set = self.ctx.find_path(schema_xpath)
            for snode in schema_set.schema():
                if (schema_xpath == snode.path()):
                    return snode
        except Exception as e:
             self.fail(e)
             return None
        else:
             for snode in schema_set.schema():
                 if schema_xapth == snode.path():
                     return snode
             return None
    """
    find_node_schema_xpath(): find the xpath of the schema node from data xpath
      data xpath example:
      "/sonic-port:sonic-port/PORT/PORT_LIST[port_name='Ethernet0']/port_name"
    input:    data_xpath - xpath of the data node
    returns:  - xpath of the schema node if success
              - Exception if error
    """
    def find_node_schema_xpath(self, data_xpath):
        path = ""
        try:
            set = self.root.find_path(data_xpath)
        except Exception as e:
            self.fail(e)
        else:
            for node in set.data():
                if data_xpath == node.path():
                    return node.schema().path()
            return path

    """
    add_node(): add a node to Yang schema or data tree
    input:    xpath and value of the node to be added
    returns:  Exception if failed
    """
    def add_node(self, xpath, value):
        try:
            node = self.new_node(xpath, value)
            #check if the node added to the data tree
            self.find_data_node(xpath)
        except Exception as e:
            print("add_node(): Failed to add data node for xpath: " + str(data_xpath))
            self.fail(e)

    """
    merge_data(): merge a data file to the existing data tree
    input:    yang model directory and full path of the data json file to be merged
    returns:  Exception if failed
    """
    def merge_data(self, data_file, yang_dir=None):
        #load all yang models to ctx
        if not yang_dir:
            yang_dir = self.yang_dir

        try:
            ctx = self.load_schema_modules_ctx(yang_dir)

            #source data node
            source_node = ctx.parse_data_path(str(data_file), ly.LYD_JSON, ly.LYD_OPT_CONFIG | ly.LYD_OPT_STRICT)

            #merge
            self.root.merge(source_node, 0)
        except Exception as e:
            self.fail(e)

    """
    delete_node(): delete a node from the schema/data tree
    input:    xpath of the schema/data node
    returns:  True - success   False - failed
    """
    def delete_node(self, data_xpath):
        try:
            node = self.find_data_node(data_xpath)
        except Exception as e:
            print("Failed to delete data node for xpath: " + str(data_xpath))
            self.fail(e)
        else:
            if (node):
                node.unlink()

    """
    find_node_value():  find the value of a node from the schema/data tree
    input:    data_xpath of the data node
    returns:  value string of the node
    """
    def find_node_value(self, data_xpath):
        output = ""
        try:
            node = self.find_data_node(data_xpath)
        except Exception as e:
            print("find_node_value(): Failed to find data node from xpath: {}".format(data_xpath))
            self.fail(e)
        else:
            if (node is not None):
                subtype = node.subtype()
                if (subtype is not None):
                    value = subtype.value_str()
                    return value
            return output

    """
    set the value of a node in the data tree
    input:    xpath of the data node
    returns:  Exception if failed
    """
    def set_dnode_value(self, data_xpath, value):
        try:
            node = self.root.new_path(self.ctx, data_xpath, str(value), ly.LYD_ANYDATA_STRING, ly.LYD_PATH_OPT_UPDATE)
        except Exception as e:
            print("set data node value failed for xpath: " + str(data_xpath))
            self.fail(e)

    """
    find_data_nodes(): find the set of nodes for the xpath
    input:    xpath of the data node
    returns:  list of xpath of the dataset
    """
    def find_data_nodes(self, data_xpath):
        list = []
        node = self.root.child()
        try:
            node_set = node.find_path(data_xpath);
        except Exception as e:
            self.fail(e)
        else:
            if node_set is None:
                raise Exception('data node not found')

            for data_set in node_set.data():
                schema = data_set.schema()
                list.append(data_set.path())
            return list

    """
    find_schema_dependencies():  find the schema dependencies from schema xpath
    input:    schema_xpath of the schema node
    returns:  - list of xpath of the dependencies
              - Exception if schema node not found
    """
    def find_schema_dependencies (self, schema_xpath):
        ref_list = []
        node = self.root
        try:
            schema_node = self.find_schema_node(schema_xpath)
        except Exception as e:
            print("Cound not find the schema node from xpath: " + str(schema_xpath))
            self.fail(e)
            return ref_list

        snode = ly.Schema_Node_Leaf(schema_node)
        backlinks = snode.backlinks()
        if backlinks.number() > 0:
            for link in backlinks.schema():
                print("backlink schema: {}".format(link.path()))
                ref_list.append(link.path())
        return ref_list

    """
    find_data_dependencies():   find the data dependencies from data xpath
    input:    data_xpath - xpath of data node
    returns:  - list of xpath
              - Exception if error
    """
    def find_data_dependencies (self, data_xpath):
        ref_list = []
        node = self.root
        try:
            data_node = self.find_data_node(data_xpath)
        except Exception as e:
            print("find_data_dependencies(): Failed to find data node from xpath: {}".format(data_xapth))
            self.fail(e)
            return ref_list

        value = str(self.find_node_value(data_xpath))

        schema_node = ly.Schema_Node_Leaf(data_node.schema())
        backlinks = schema_node.backlinks()
        if backlinks.number() > 0:
            for link in backlinks.schema():
                 node_set = node.find_path(link.path())
                 for data_set in node_set.data():
                      schema = data_set.schema()
                      casted = data_set.subtype()
                      if value == casted.value_str():
                          ref_list.append(data_set.path())

        return ref_list

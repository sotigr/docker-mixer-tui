#!/usr/bin/env python3

try:
    import yaml
except ImportError:
    print("The yaml package is missing, try to install with 'pip3 install yaml'")
    exit()
try:
    import textual       
except ImportError:
    print("The textual package is missing, try to install with 'pip3 install textual==0.30.0'")
    exit()
try:
    import pathlib       
except ImportError:
    print("The pathlib package is missing, try to install with 'pip3 install pathlib'")
    exit()

from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll, Container, ScrollableContainer
from textual.binding import Binding
from textual.widgets import Button, ContentSwitcher,Input, LoadingIndicator, Checkbox, Footer, Label, Static, OptionList, DirectoryTree
from textual.widgets.option_list import Option  
import sys
import json
import yaml 
from os.path import exists 
import os
from pathlib import Path
  
class Manager(App[None]): 

    BINDINGS = [
        Binding(key="q", action="quit", description="Press q to quit"),
        Binding(key="g", action="generate", description="Press g to regenerate the yml"),
    ]

    def action_generate(self) -> None:
        self.save_config()

    CSS = """
        Screen {
            align: center middle;
            padding: 1;
        }

        #buttons {
            height: 3;
            width: auto;
        }
 
        #output {
            background: black;
            padding: 1;
        }
        .hide {
            display: none;
        } 
        ContentSwitcher {
            background: $panel;
            border: round $primary;
            width: 100%;
            height: 1fr;
        }
  
        MarkdownH2 {
            background: $primary;
            color: yellow;
            border: none;
            padding: 0;
        } 

        .out_inner {
            min-height: 8;
        }
        .out {
            height: 10;
        }
        .margin {
            margin: 1;
        } 
        .button_container {
            height: 5;
        }
        .lists {
            height: 10; 
        }
        .msg {
            max-height: 3;
        }
    """
    def compose(self) -> ComposeResult:
        path = "./" if len(sys.argv) < 2 else sys.argv[1] 
        yield Label(id="message") 

        with Horizontal(id="buttons"):    
            yield Button("Active Services", id="active_services_view")  
            yield Button("Logs", id="logs_view")  
            yield Button("Environment", id="env_view")  


        with Container( id="loading_container", classes="hide"  ):
            yield LoadingIndicator()
        with ContentSwitcher(initial="active_services_view", id="content"):  
             

            # TAB 1
            with VerticalScroll(id="active_services_view"):
                with ContentSwitcher(id="yaml_switcher", initial="yaml_view"):
                    yield VerticalScroll(
                        # Button("Save/Reload config", variant="primary", classes="margin", id="reload_cfg_btn"),
                        Static("Yaml files:", classes="margin"),
                        OptionList(id="yaml_list", classes="lists"),
                        Horizontal(
                            Button("Add", variant="primary", classes="margin", id="add_yaml_btn"),
                            Button("Remove", variant="error", classes="margin", id="remove_yaml_btn"), 
                            classes="button_container"
                        ),

                        Static("Disabled services:", classes="margin"),
                        OptionList(id="disabled_services", classes="lists"),
                        Horizontal(
                            Button("Add", variant="primary", classes="margin", id="add_disabled__btn"),
                            Button("Remove", variant="error", classes="margin", id="remove_disabled_btn"), 
                            classes="button_container"
                        ),

                        id="yaml_view"
                    )
                    yield VerticalScroll(
                        DirectoryTree(path, id="yaml_tree_view"),
                        Horizontal(
                            Button("Cancel", classes="margin", id="cancel_yaml_file"),
                            Button("Select File", variant="primary", classes="margin", id="select_yaml_file")
                        ),
                        id="yaml_select_view"
                    )
                    yield VerticalScroll(
                        OptionList(id="list_disabled", classes="lists"),
                        Horizontal(
                            Button("Cancel", classes="margin", id="cancel_select_disabled"),
                            Button("Select Service", variant="primary", classes="margin", id="select_disabled")
                        ),
                        id="disabled_select_view"
                    )
            # TAB 2
            with Container(id="logs_view"):
                yield ScrollableContainer( id="log_items_container")
                
            with VerticalScroll(id="env_view"):
 
                yield Static(".env files:", classes="margin")
                yield OptionList(id="env_file_list", classes="lists")
                yield Horizontal(
                    Button("Add", variant="primary", classes="margin", id="add_env_btn"),
                    Button("Remove", variant="error", classes="margin", id="remove_env_btn"), 
                    classes="button_container"
                )

                yield Static(".env output (Press 'Enter' to apply):", classes="margin")
                yield Input(placeholder="ex: ./.env", id="input_env_output")

                yield Static("docker context (Press 'Enter' to apply):", classes="margin")
                yield Input(placeholder="ex: ../",  id="input_docker_context")
                    
                yield Static("docker-compose yml output (Press 'Enter' to apply):", classes="margin")
                yield Input(placeholder="ex: ./docker-compose.yml",  id="input_compose_yml_out")
                
            with VerticalScroll(id="env_select_view"):
                yield DirectoryTree(path, id="env_select_tree")
                yield Horizontal(
                    Button("Cancel", classes="margin", id="cancel_select_env_btn"),
                    Button("Select File", variant="primary", classes="margin", id="select_env_btn")
                )
                
        yield Footer()

    def set_loading(self, flag):
        if flag == True:
            self.query_one("#loading_container", Container).remove_class("hide")
            self.query_one("#content", ContentSwitcher).add_class("hide") 
        else:
            self.query_one("#loading_container", Container).add_class("hide")
            self.query_one("#content", ContentSwitcher).remove_class("hide") 

    # Use this method only for debugging
    def set_message(self, message, msgType="default"):
        style = ""
        if msgType == "error":
            style = "background: maroon; color: white; display: block;"
        elif  msgType == "info":
            style = "background: lightblue; color: white; display: block;"
        else:
            style = " display: block;"
        if message == "": 
            self.query_one("#message", Label).set_styles("display: none;")
        else:
            self.query_one("#message", Label).set_styles(style).update(message)

    def on_directory_tree_file_selected(
            self, event: DirectoryTree.FileSelected
        ) -> None:
        event.stop() 
        path = event.path 
        self.current_file_path = "./" + str(path)

    def on_checkbox_changed(self):
        self.save_config()

    def on_input_submitted(self, event: Input.Submitted)-> None:
        self.save_config()

    def on_option_list_option_selected(
            self, event: OptionList.OptionSelected
        ) -> None:
        
        if event.option_list.id == "yaml_list":
            self.yaml_list_selected_id = event.option_id 
        elif event.option_list.id == "list_disabled":
            self.disabled_list_selected_id = event.option_id 
        elif event.option_list.id == "disabled_services":
            self.disabled_current_list_selected_id = event.option_id 
        elif event.option_list.id == "env_file_list":
            self.env_list_selected_id = event.option_id 

    def on_button_pressed(self, event: Button.Pressed) -> None:
        
        if event.button.id == "add_yaml_btn":
            self.query_one("#yaml_switcher", ContentSwitcher).current = "yaml_select_view"  
        elif  event.button.id == "cancel_yaml_file":
            self.query_one("#yaml_switcher", ContentSwitcher).current = "yaml_view"
        elif event.button.id == "select_yaml_file":
            file_path = self.current_file_path
            if file_path.endswith("yaml") or file_path.endswith("yml"): 
                lst = self.query_one("#yaml_list", OptionList) 
                lst.add_option(Option(file_path, id=file_path))
                self.query_one("#yaml_switcher", ContentSwitcher).current = "yaml_view"  
                self.save_config()
            else:
                return
        elif event.button.id == "remove_yaml_btn": 
            try:
                lst = self.query_one("#yaml_list", OptionList)
                lst.remove_option(self.yaml_list_selected_id)
                self.save_config()
            except:
                pass

        elif  event.button.id == "add_disabled__btn":
            self.query_one("#yaml_switcher", ContentSwitcher).current = "disabled_select_view"

        elif  event.button.id == "cancel_select_disabled":
            self.query_one("#yaml_switcher", ContentSwitcher).current = "yaml_view"
        elif  event.button.id == "select_disabled": 
            dlst = self.query_one("#disabled_services", OptionList) 
            dlst.add_option(Option(self.disabled_list_selected_id, id=self.disabled_list_selected_id))
            self.save_config()
            self.query_one("#yaml_switcher", ContentSwitcher).current = "yaml_view"
        elif event.button.id == "remove_disabled_btn":
            try:
                lst = self.query_one("#disabled_services", OptionList)
                lst.remove_option(self.disabled_current_list_selected_id)
                self.save_config()
            except:
                pass
        elif  event.button.id == "reload_cfg_btn": 
            self.save_config()

        elif event.button.id == "add_env_btn": 
          self.query_one("#content", ContentSwitcher).current = "env_select_view"
        elif  event.button.id == "cancel_select_env_btn": 
          self.query_one("#content", ContentSwitcher).current = "env_view"
        elif  event.button.id == "select_env_btn": 
            file_path = self.current_file_path 
            lst = self.query_one("#env_file_list", OptionList) 
            lst.add_option(Option(file_path, id=file_path))
            self.query_one("#content", ContentSwitcher).current = "env_view"  
            self.save_config()
        elif event.button.id =="remove_env_btn":
            try:
                lst = self.query_one("#env_file_list", OptionList)
                lst.remove_option(self.env_list_selected_id)
                self.save_config()
            except:
                pass
        else:  
            self.query_one("#content", ContentSwitcher).current = event.button.id  

    def create_default_config(self):
        out = {}
        out["context"] = "./"
        out["configs"] = []
        out["logOnly"] = []
        out["excludeServices"] = []
        out["envFiles"] = []
        out["output"] = "./docker-compose.yml"
        out["outputEnv"] = "./.env"
        f = open("config.json", "w")
        f.write(json.dumps(out, indent=2))
        f.close()
        self.load_config()

    def load_config(self):
        if not exists("config.json"):
            self.create_default_config()
            return
        def get_services(file):    
            f = open(file)
            ml = yaml.safe_load(f)
            f.close() 
            return ml["services"]
        
        self.query_one("#yaml_list", OptionList).clear_options()
        self.query_one("#list_disabled", OptionList).clear_options()
        self.query_one("#disabled_services", OptionList).clear_options()
        self.query_one("#env_file_list", OptionList).clear_options()
        self.query_one("#log_items_container", ScrollableContainer).remove_children()
 
        services = {}
        f = open("config.json")
        config = json.load(f)
        f.close()
        self._config = config
        self.query_one("#input_compose_yml_out", Input).value = config["output"]
        self.query_one("#input_env_output", Input).value = config["outputEnv"]
        self.query_one("#input_docker_context", Input).value = config["context"]

        for path in config["envFiles"]:
            lst = self.query_one("#env_file_list", OptionList) 
            lst.add_option(Option(path, id=path))  
            
        for path in config["configs"]:
            lst = self.query_one("#yaml_list", OptionList)  
            lst.add_option(Option(path, id=path)) 
            services = {**services, **get_services(path)}  
            
        self.services = services

        dlst = self.query_one("#list_disabled", OptionList) 
        lic = self.query_one("#log_items_container", ScrollableContainer) 
        for key in services:
            if not key in config["excludeServices"]:
                dlst.add_option(Option(key, id=key))
            selected = key in config["logOnly"]
            lic.mount (
                Checkbox(key, value=selected, id="ch"+key),    
            )

        for path in config["excludeServices"]:
            dlst = self.query_one("#disabled_services", OptionList)  
            if path in services:
                dlst.add_option(Option(path, id=path)) 
       

    def save_config(self):
        out = {}
        out["context"] = self.query_one("#input_docker_context", Input).value
        out["configs"] = []
        out["logOnly"] = []
        out["envFiles"] = []
        out["excludeServices"] = []
        out["output"] = self.query_one("#input_compose_yml_out", Input).value
        out["outputEnv"] = self.query_one("#input_env_output", Input).value
  
        evls = self.query_one("#env_file_list", OptionList)
        for c in evls._options:
            out["envFiles"].append(c.id)

        ymls = self.query_one("#yaml_list", OptionList)
        for c in ymls._options:
            out["configs"].append(c.id)

        sls = self.query_one("#disabled_services", OptionList)
        for c in sls._options:
            out["excludeServices"].append(c.id)

        for key in self.services:
            ch = self.query_one("#ch"+key, Checkbox)
            if ch.value == True:
                out["logOnly"].append(key)
        f = open("config.json", "w")
        f.write(json.dumps(out, indent=2))
        f.close()

        self.load_config()
        self.generate_output()

    def generate_output(self):
        config = self._config 

        outObject = {
            "version": "3.7",
            "services": {}
        }

        workDir = os.path.abspath(config["context"])
        for c in config["configs"]:
            cPath = os.path.join(workDir, os.path.abspath(c))
            cf = open(cPath)
             
            ymlObject = yaml.safe_load(cf)
            for name, service in ymlObject["services"].items():
                if name in config["excludeServices"]:
                    continue
                if "build" in service:
                    if "context" in service["build"]: 
                        service["build"]["context"] = "./" + str(Path(os.path.dirname(c)).joinpath(service["build"]["context"]))
                    elif isinstance(service["build"], str):
                        service["build"] ="./" + str(Path(os.path.dirname(c)).joinpath(service["build"]))
                if "volumes" in service: 
                        service["volumes"] = [ "./" + str(Path(os.path.dirname(c)).joinpath(v)) for v in service["volumes"] ]
                if name in outObject["services"]:
                    print("Error: Duplicate service named '" + name + "' found. All services must have a unique name.")
                    exit(-1)
                
                if "logOnly" in config: 
                    if name not in config["logOnly"]:
                        service["logging"] = {
                            "driver": "none"
                        }
                outObject["services"][name] = service


        f = open(config["output"], "w")
        f.write(yaml.dump(outObject))
        f.close()
  
        out_dot_env = ""
        for dot_env in config["envFiles"]:
            env_path = os.path.join(workDir, dot_env) 
            if not os.path.exists(env_path):
                continue
            with open(env_path, "r") as file:
                strv = file.read()
                out_dot_env += strv + "\n"

        output_env_path =   config["outputEnv"]
        with open(output_env_path, "w") as file:
            file.write(out_dot_env)


    def on_mount(self) -> None:
        self.load_config()


if __name__ == "__main__":
    Manager().run()
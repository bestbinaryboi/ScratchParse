#!/usr/bin/env python3
"""
Scratch Project Editor - Simplified interface for editing project.json

This tool provides a simpler format for editing Scratch project data and
automatically recompiles it back to the original format.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


class ScratchProjectEditor:
    def __init__(self, project_file: str = "project.json"):
        """Initialize the editor with a project file."""
        self.project_file = Path(project_file)
        self.data = self._load_project()
        self.simplified = {}
        
    def _load_project(self) -> Dict[str, Any]:
        """Load the project.json file."""
        if not self.project_file.exists():
            raise FileNotFoundError(f"Project file not found: {self.project_file}")
        
        with open(self.project_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def to_simplified(self) -> Dict[str, Any]:
        """Convert project data to simplified format for editing."""
        simplified = {}
        
        if "targets" in self.data:
            simplified["targets"] = []
            for target in self.data["targets"]:
                simple_target = {
                    "name": target.get("name", ""),
                    "isStage": target.get("isStage", False),
                    "variables": self._simplify_variables(target.get("variables", {})),
                    "lists": self._simplify_lists(target.get("lists", {})),
                    "broadcasts": list(target.get("broadcasts", {}).keys()),
                    "blocks": self._simplify_blocks(target.get("blocks", {})),
                    "costumes": self._simplify_costumes(target.get("costumes", [])),
                    "sounds": self._simplify_sounds(target.get("sounds", [])),
                }
                simplified["targets"].append(simple_target)
        
        if "meta" in self.data:
            simplified["meta"] = self.data["meta"]
        
        self.simplified = simplified
        return simplified
    
    def _simplify_variables(self, variables: Dict) -> Dict[str, str]:
        """Simplify variable format: {id: [name, value]} -> {name: value}"""
        simplified = {}
        for var_id, var_data in variables.items():
            if isinstance(var_data, list) and len(var_data) >= 2:
                name = var_data[0]
                value = var_data[1]
                simplified[name] = value
        return simplified
    
    def _simplify_lists(self, lists: Dict) -> Dict[str, List]:
        """Simplify list format: {id: [name, items]} -> {name: items}"""
        simplified = {}
        for list_id, list_data in lists.items():
            if isinstance(list_data, list) and len(list_data) >= 2:
                name = list_data[0]
                items = list_data[1]
                simplified[name] = items
        return simplified
    
    def _simplify_blocks(self, blocks: Dict) -> Dict[str, Dict]:
        """Extract key information from blocks."""
        simplified = {}
        for block_id, block_data in blocks.items():
            simplified[block_id] = {
                "opcode": block_data.get("opcode", ""),
                "next": block_data.get("next"),
                "parent": block_data.get("parent"),
                "inputs": block_data.get("inputs", {}),
                "fields": block_data.get("fields", {}),
                "topLevel": block_data.get("topLevel", False),
            }
        return simplified
    
    def _simplify_costumes(self, costumes: List) -> List[Dict]:
        """Simplify costume data."""
        simplified = []
        for costume in costumes:
            simplified.append({
                "name": costume.get("name", ""),
                "dataFormat": costume.get("dataFormat", ""),
                "assetId": costume.get("assetId", ""),
            })
        return simplified
    
    def _simplify_sounds(self, sounds: List) -> List[Dict]:
        """Simplify sound data."""
        simplified = []
        for sound in sounds:
            simplified.append({
                "name": sound.get("name", ""),
                "assetId": sound.get("assetId", ""),
                "rate": sound.get("rate", 48000),
                "sampleCount": sound.get("sampleCount", 0),
            })
        return simplified
    
    def from_simplified(self, simplified: Dict[str, Any]) -> Dict[str, Any]:
        """Convert simplified format back to original project format."""
        restored = self.data.copy()
        
        if "targets" in simplified:
            restored["targets"] = []
            for i, simple_target in enumerate(simplified["targets"]):
                original_target = self.data["targets"][i] if i < len(self.data["targets"]) else {}
                
                restored_target = original_target.copy()
                
                # Restore variables
                if "variables" in simple_target:
                    variables = {}
                    for name, value in simple_target["variables"].items():
                        # Try to find the original ID
                        var_id = self._find_variable_id(original_target, name)
                        variables[var_id] = [name, value]
                    restored_target["variables"] = variables
                
                # Restore lists
                if "lists" in simple_target:
                    lists = {}
                    for name, items in simple_target["lists"].items():
                        list_id = self._find_list_id(original_target, name)
                        lists[list_id] = [name, items]
                    restored_target["lists"] = lists
                
                # Restore broadcasts
                if "broadcasts" in simple_target and "broadcasts" in original_target:
                    broadcasts = {}
                    for broadcast_name in simple_target["broadcasts"]:
                        # Try to find the original broadcast ID
                        for bcast_id, bcast_name in original_target.get("broadcasts", {}).items():
                            if bcast_name == broadcast_name:
                                broadcasts[bcast_id] = broadcast_name
                                break
                    restored_target["broadcasts"] = broadcasts
                
                restored["targets"].append(restored_target)
        
        return restored
    
    def _find_variable_id(self, target: Dict, name: str) -> str:
        """Find the ID of a variable by name."""
        for var_id, var_data in target.get("variables", {}).items():
            if isinstance(var_data, list) and var_data[0] == name:
                return var_id
        return f"var_{name}"  # Fallback: create new ID
    
    def _find_list_id(self, target: Dict, name: str) -> str:
        """Find the ID of a list by name."""
        for list_id, list_data in target.get("lists", {}).items():
            if isinstance(list_data, list) and list_data[0] == name:
                return list_id
        return f"list_{name}"  # Fallback: create new ID
    
    def save_simplified(self, output_file: str = "project_simplified.json"):
        """Save the simplified format to a file."""
        if not self.simplified:
            self.to_simplified()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.simplified, f, indent=2)
        print(f"Simplified project saved to {output_file}")
    
    def load_simplified(self, input_file: str = "project_simplified.json") -> Dict[str, Any]:
        """Load simplified format from a file."""
        with open(input_file, 'r', encoding='utf-8') as f:
            self.simplified = json.load(f)
        return self.simplified
    
    def save_project(self, output_file: str = None):
        """Save the modified project back to JSON."""
        if output_file is None:
            output_file = str(self.project_file)
        
        # Convert from simplified back to original format
        restored = self.from_simplified(self.simplified)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(restored, f, separators=(',', ':'))
        print(f"Project saved to {output_file}")


def main():
    """Command-line interface for the editor."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python project_editor.py export             - Export to simplified format")
        print("  python project_editor.py import <file>      - Import from simplified format")
        print("  python project_editor.py show               - Show simplified format")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        editor = ScratchProjectEditor()
        
        if command == "export":
            editor.to_simplified()
            editor.save_simplified()
            print("✓ Exported to project_simplified.json")
        
        elif command == "import":
            if len(sys.argv) < 3:
                print("Error: Missing input file")
                sys.exit(1)
            editor.load_simplified(sys.argv[2])
            editor.save_project()
            print(f"✓ Imported from {sys.argv[2]} and saved to {editor.project_file}")
        
        elif command == "show":
            simplified = editor.to_simplified()
            print(json.dumps(simplified, indent=2))
        
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

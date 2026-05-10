# Python

LooseMan@MacBookPro c_prog % python -m venv .venv
LooseMan@MacBookPro c_prog % source .venv/bin/activate

% pip install --upgrade pip
% pip install pip-tools

(.venv) LooseMan@MacBookPro c_prog % pip install -r requirements.txt 
Collecting tree-sitter==0.25.2 (from -r requirements.txt (line 7))
  Using cached tree_sitter-0.25.2-cp312-cp312-macosx_10_13_x86_64.whl.metadata (10.0 kB)
Collecting tree-sitter-cpp==0.23.4 (from -r requirements.txt (line 9))
  Using cached tree_sitter_cpp-0.23.4-cp39-abi3-macosx_10_9_x86_64.whl.metadata (1.8 kB)
Using cached tree_sitter-0.25.2-cp312-cp312-macosx_10_13_x86_64.whl (146 kB)
Using cached tree_sitter_cpp-0.23.4-cp39-abi3-macosx_10_9_x86_64.whl (287 kB)
Installing collected packages: tree-sitter-cpp, tree-sitter
Successfully installed tree-sitter-0.25.2 tree-sitter-cpp-0.23.4

[notice] A new release of pip is available: 24.0 -> 26.1.1
[notice] To update, run: pip install --upgrade pip
(.venv) LooseMan@MacBookPro c_prog % pip list 
Package         Version
--------------- -------
pip             24.0
tree-sitter     0.25.2
tree-sitter-cpp 0.23.4

[notice] A new release of pip is available: 24.0 -> 26.1.1
[notice] To update, run: pip install --upgrade pip
(.venv) LooseMan@MacBookPro c_prog % 

jinja2==3.1.6
tree-sitter==0.25.2
tree-sitter-cpp==0.23.4

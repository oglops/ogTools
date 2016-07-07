# ogTools
misc tools

## Usage 举例
```python
# 得到import进来的所有新nodes
from mayaDecorators import capturenewnodes

with capturenewnodes() as nodes:
    doSomething
    
new_nodes = nodes.get_nodes()

# bake曲线或者需要动timeline的脚本时，不显示viewport以加快速度
from mayaDecorators import disableviewport,disableundo

@disableundo
@disableviewport
def slowFunc():
    doSomething
    
...
slowFunc()
```

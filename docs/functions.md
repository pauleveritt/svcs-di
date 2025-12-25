# Injecting functions

In `tdom` we can write components as functions. These function components will want toa void "prop drilling". But `svcs`
is based around *types* -- meaning classes or protocols.

How can we use `svcs` for injection while keeping the simplicity of function cmoponents, without requiring a protocol?

Then later, in the more-advanced injector, how can we allow **replaceable** components 

## How Hopscotch does it

- Look at the concept of [kind](https://hopscotch.readthedocs.io/en/latest/registry.html#kind)
- The implementation [is in class Registry here](/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py)

## How `svcs-di` might do it

- Minimal approach
  - Register a `FunctionInjector`
  - `tdom` can use it when the component is a function
  - The component function can then have parameters that are `Injectable`
  - But this means function components can't be "replaceable" without a decorator and a protocol

## To Do

- Make sure `auto.py` doesn't have any "extra" stuff that might be objectionable
- 
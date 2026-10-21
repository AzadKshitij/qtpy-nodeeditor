Every serializable object implements this interface, which is what makes
scenes savable to JSON.

`Serializable` provides the `id` attribute that every serialized object
carries, and defines two methods for child classes to override:

- `serialize()` — return the object's state as a dictionary
- `deserialize(data, hashmap)` — restore the object from that dictionary

The data uses an `OrderedDict` rather than a plain `dict`, so the order of
the parameters in the file is stable.

The classes deriving from `Serializable` are `Scene`, `Node`, `Edge`, `Socket`
and the node content widgets.

::: nodeeditor.node_serializable

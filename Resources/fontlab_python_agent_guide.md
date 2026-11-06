# FontLab Python scripting guide

Use Python 3 inside FontLab for font-model and editor operations. External Python can use the MCP bridge, but it does not automatically have access to FontLab's embedded modules or open documents.

## API selection

```python
import fontlab as fl
import fontgate as fg  # Only when using the FontGate model.
from PythonQt import QtCore, QtGui
```

Use the installed API. Do not borrow method names from Glyphs, RoboFont, FontForge, PyQt, or PySide. Optional wrappers must be explicitly available in the project. `hasattr` establishes that a name exists, not its signature or side effects.

Prefer focused native MCP tools when they fully match the request. Distinguish writing a script from executing it, and follow the host's authorization controls.

## Objects and targets

| Expression | Result or form |
|---|---|
| `fl.CurrentFont()` | Current FontGate `fgFont`, or `None` |
| `fl.CurrentGlyph()` | Current FontGate `fgGlyph`, or `None` |
| `fl.flPackage(fg_font)` | Editor package wrapper |
| `package.findName(name)` | Editor `flGlyph` |
| `glyph.findLayer(name)` | Existing layer; does not create it |
| `glyph.findLayerCreate(name)` | May create a layer; use only when intended |
| `glyph.layers`, `glyph.activeLayer` | Properties |
| `layer.shapes`, `shape.contours` | Properties |
| `contour.nodes()` | Method |
| `node.x`, `node.y`, `layer.advanceWidth` | Properties |
| `shape.transform` | Qt transform property |
| `shape.isComponent`, `shape.isComposite` | Boolean properties |
| `glyph.inkBox()` | Editor glyph method |

Resolve explicit names before mutation:

```python
import fontlab as fl


def resolve(glyph_name, layer_name):
    font = fl.CurrentFont()
    if font is None:
        raise RuntimeError("No current font")
    package = fl.flPackage(font)
    glyph = package.findName(glyph_name)
    if not glyph:
        raise ValueError("Missing glyph: " + glyph_name)
    layer = glyph.findLayer(layer_name)
    if not layer:
        raise ValueError("Missing layer: " + layer_name)
    return package, glyph, layer
```

The active glyph, selected glyphs, and all glyphs are different scopes. Do not silently substitute one for another. Capture the target package once instead of following focus changes inside a loop. A layer's position in a list does not identify its master.

## Plan before editing

Validate all names, finite numeric values, and layer constraints first. Compute a preview without calling setters, creating layers, sending change notifications, changing selection, or writing files. Never implement a preview by editing and then calling Undo.

Reject missing targets unless creation was requested. Handle locked layers, automatic layers, and driven metrics explicitly. Do not silently detach expressions, alter preferences, or decompose components.

For batches, record completed targets. An exception does not roll back earlier native edits. Stop after failure and report partial completion. Avoid replaying additive edits after a timeout; their outcome may be unknown.

## History and notifications

Mutation, cache refresh, Undo enrollment, redraw, and saving are separate responsibilities. For direct edits to existing editor layers/glyphs, use the scoped notification pattern supported by the installed build:

```python
# Fragment: glyph and layer are resolved; the requested edit is validated.
import fontlab as fl

title = "Set layer width"
fl.flItems.notifyChangesApplied(title, [layer, glyph])
try:
    layer.advanceWidth = 640.0
finally:
    fl.flItems.notifyChangesApplied(title, [layer, glyph])
```

Recursive history is enabled by default in this binding. Keep it enabled for nested geometry. The object list identifies what needs history and geometry refresh. A no-argument notification is not a substitute for supplying the edited objects.

The pattern is not a rollback transaction. A final notification records/refreshes possible partial edits; it does not undo them. Confirm Undo/Redo behavior for the operation before promising it. Do not add redundant notifications around an already undo-managed MCP operation.

`glyph.update()` and `fl.Update(glyph)` do not replace a verified history workflow. `AcceptChanges()` participates in change-controller processing; do not call it as a generic cleanup operation. Do not invent `font.updateGlyph`.

## Geometry

Know whether coordinates are contour-local, shape-local, layer coordinates, or canvas coordinates. An element transform can make stored node coordinates differ from visible positions. To move one component instance, change its placement rather than editing its source glyph.

Maintain contour closure, start point, node order, names, and handles. Native node kinds are `on` for endpoints, `curve` for cubic handles, and `off` for quadratic handles. Cubic segments normally have two handles between endpoints; quadratic chains can imply intermediate on-curve points.

Build unattached native geometry with explicit node types:

```python
import fontlab as fl
from PythonQt import QtCore

nodes = [fl.flNode(QtCore.QPointF(x, y), nodeType="on")
         for x, y in ((50, 0), (550, 0), (550, 700), (50, 700))]
contour = fl.flContour(nodes, closed=True)
shape = fl.flShape()
shape.addContour(contour, True)
```

Attach it with `layer.addShape(shape)` inside the appropriate mutation workflow. Appending to a returned Python list is not necessarily a native insertion. Lists can contain live wrappers without being live membership containers.

Delete original node indices in descending order or recompute indices after each membership change. Do not treat all points as independent endpoints. Preserve shared shape data unless independent copies are explicitly requested.

For `QtGui.QTransform(a, b, c, d, tx, ty)`:

```text
x_new = a*x + c*y + tx
y_new = b*x + d*y + ty
```

Assigning `shape.transform` replaces its existing placement. Preserve scale, rotation, reflection, and shear when the request is only a translation. Verify composition order with a known point. FontGate matrices and serialized transform objects have separate contracts.

Distinguish stored bounds from rendered ink bounds. Refresh the affected geometry before measuring edited results. Font y normally increases upward; `QRectF.top()` and `bottom()` follow numeric rectangle conventions. Use explicit minima/maxima rather than assuming “top” means the glyph's highest point. Bézier control-point bounds are not exact curve extrema.

## Components and live construction

The supported component append form accepts one argument:

```python
# Fragment: glyph/layer are resolved; source H exists in the target font.
import fontlab as fl
from PythonQt import QtGui

fl.flItems.notifyChangesApplied("Add component", [layer, glyph])
layer.addComponent(("H", QtGui.QTransform(1, 0, 0, 1, 30, 10)))
fl.flItems.notifyChangesApplied("Add component", [layer, glyph])
```

`addComponent` returns `None`, not the added shape. Reinspect the layer to find it. Repeating the call adds another component, so define a duplicate policy. The binding uses the destination layer name for source resolution; cross-layer construction needs a separately verified API or schema-backed VFJ edit.

`setGlyphComponents(components, width, package, colorize, flags=0)` replaces shape content. Its legacy tuples use `(name_id, transform, width_scale, use_anchors)`, unlike `addComponent`. `package.generateGlyph(...)` returns component data, not a guaranteed `(components, width)` pair.

Groups and live builders can regenerate derived contours. Edit defining inputs where appropriate. Do not permanently edit generated outlines or detach shared sources without understanding the consequences.

## Anchors, hints, masters, and metadata

Anchors can have expressions, cloud/mark settings, and shape bindings. Preserve them unless an explicit override is required. Use an update-or-reject policy for duplicate names. Fractional values can be affected by the editor's rounding preference; read back results and never silently change global preferences.

PostScript hint records, detected stems, guidelines, and TrueType instructions are distinct. A hint can be driven by a node link or expression. Discover focused hint tools and use explicit detachment only when requested.

For multi-master changes, identify every target layer. Preserve masks, service layers, master locations, and interpolation metadata. Structural compatibility includes contour order, start points, node kinds, and component order—not just equal node counts.

Glyph names, Unicode values, list indices, and native IDs are different identifiers. Preserve multiple encodings and non-BMP values. Verify lookup behavior as well as stored values after changes. A zero kerning pair and a deleted exception can behave differently through class inheritance; resolve the intended master and classes.

Prefer focused metadata setters. Keep Sigma and other extensible dictionaries intact during unrelated edits.

## Ownership and lifetime

Do not assume a Python list, wrapper constructor, or `copy.deepcopy()` creates an independent native object graph. Reacquire objects after deletion, whole-glyph replacement, Undo/Redo, or document close/reopen.

After inserting a FontGate glyph through `flPackage.addGlyph`, reacquire the editor glyph with `package.findName(name)`. Verify ownership/copy behavior in the installed binding before using temporary objects. A redraw does not establish native ownership or update every lookup cache.

Keep editor mutations on the GUI thread. Reuse the application's Qt event loop; do not construct another `QApplication`. Do not retain borrowed events or painters after callbacks. Unregister callbacks/tools when reloading or closing them. Avoid font mutations inside paint callbacks.

## MCP from Python

```python
# Fragment: package is an explicitly resolved flPackage.
import fontpr

if not fontpr.available():
    raise RuntimeError("MCP tools are not ready")
tools = {tool["name"]: tool for tool in fontpr.list_tools()}
if "get_glyph" not in tools:
    raise RuntimeError("get_glyph is unavailable")
data = fontpr.call("get_glyph", font_id=int(package.fgId), glyph_name="A")
```

Pass tool parameters by keyword. Failures raise `fontpr.Error`; stop dependent edits after a failure. JSON numbers can arrive as floats, so validate that indices are integral before conversion. `run_python` and `get_python_output` cannot be called recursively through `fontpr`.

For full-glyph changes, fetch writable `get_glyph` output, consult `get_vfj_schema`, modify only intended fields, use advertised `dry_run` support, commit, then read back. `set_glyph` replaces the whole glyph, including layers. Pass a dictionary, not `json.dumps(data)`. Construction summaries are not writable VFJ.

Ordinary VFJ component transforms belong on the enclosing element beside `component`; they use named coefficients. Some builder dictionaries use different matrix forms. Consult the exact topic instead of globally rewriting every `transform` field.

## Saving and verification

Save only to authorized paths and formats. Native save, save-copy, and export have different contracts. `flPackage.close(prompt=True)` controls prompting; `close(False)` can discard unsaved edits and does not mean “save.” Inspect the installed save API rather than inferring behavior from a filename extension.

Verify requested values on fresh readback and preserve unrelated layers, geometry, encodings, and metadata. Use exact comparisons for identifiers and discrete results, and justified tolerances for floating geometry. Check Undo/Redo and saved-file reopening when those guarantees matter.

Keep diagnostics bounded. Report targets, completed changes, skipped items, failures, verification performed, and saved paths. Do not report success after an edit error or claim execution from a generated script alone.

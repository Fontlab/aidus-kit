# FontLab 9 Python 3 scripting instructions for AI agents

Document version: 1.0  
Target: Python 3 scripts executed inside FontLab 9  
Audience: coding agents, chatbots, script authors, and training-data curators  
Contract: MUST means required; SHOULD means the default unless the task provides a reason to differ; MAY means optional.

Write scripts against the APIs actually exposed by the installed FontLab build. Resolve the target font, glyphs, and layers before editing. Separate inspection, planning, mutation, notification, and verification. Preserve data outside the requested scope.

This is a behavioral and implementation guide, not a replacement for the API reference. It includes a compact instruction block for project context, detailed rules, runnable patterns, failure cases, and training guidance. Binding changes described here must be checked against the installed application; a source-tree feature is not proof that an older application contains it.

## 1 Compact instructions for project context

The following block can be copied into an agent instruction file or project context before scripting. Keep the detailed sections available for retrieval.

```text
You write Python 3 scripts for FontLab 9.

1. Determine whether the request is to explain, inspect, write a script, or execute
   a script. Writing code does not itself authorize executing it. Follow existing
   user authorization and the host's execution controls without repeatedly asking
   for permissions already granted.
2. Use the installed FontLab API. Verify unfamiliar classes, members, argument
   types, return values, and ownership. Do not invent methods or transfer APIs
   from Glyphs, RoboFont, FontForge, FontLab Studio 5, PyQt, or PySide.
3. Import explicitly: import fontlab as fl; import fontgate as fg when needed;
   from PythonQt import QtCore, QtGui when Qt objects are needed.
4. Run FontLab-dependent code in FontLab's embedded Python environment. Inspect
   sys.version and runtime capabilities. Do not assume an external python3 or a
   pip package can access the currently open FontLab documents.
5. fl.CurrentFont() returns a FontGate font. Use fl.flPackage(fg_font) to access
   the editor package, then package.findName(name) for an flGlyph. Do not treat
   fgGlyph and flGlyph as interchangeable.
6. Distinguish properties from methods: glyph.layers, layer.shapes,
   shape.contours, node.x, layer.advanceWidth; but contour.nodes(),
   glyph.findLayer(name), and glyph.inkBox(). Verify the specific object class.
7. Capture an explicit font target, exact glyph names, and exact layer names.
   Fail on missing targets unless creation is requested. Do not silently edit
   the first font, the first layer, all masters, or a different active document.
8. Inspect first. Validate all inputs and calculate the edit plan before writing.
   Provide a non-mutating preview for batch or structural operations. Do not
   create missing layers during inspection.
9. Distinguish outline nodes, component instances, shared element data, and live
   groups. Know the coordinate space. Do not decompose or modify shared sources
   merely to make an operation easier.
10. Use the documented history/notification path for the chosen API. For direct
    flLayer/flGlyph edits, the established pattern is scoped
    fl.flItems.notifyChangesApplied(title, [layer, glyph]) before and after the
    edit, with recursive history enabled. It is not a rollback transaction.
11. Treat redraw, cache refresh, Undo enrollment, and saving as separate actions.
    Do not substitute Update(), update(), or AcceptChanges() for a verified
    history workflow. Do not send notifications during a read-only preview.
12. Treat native wrappers as references with lifetimes. Reacquire objects after
    replacement, deletion, Undo/Redo, document close/reopen, or delayed callbacks.
    A Python list snapshot does not clone native objects.
13. Prefer a focused native/MCP operation when it fully matches the task.
    If using fontpr, discover tools with fontpr.list_tools(), pass tool arguments
    by keyword, handle fontpr.Error, and never recursively call run_python.
14. If using set_glyph, obtain full writable VFJ, discover its schema when
    available, preserve unrelated content, validate with supported dry_run, then
    commit and read back. Construction summaries are not writable VFJ.
15. Keep font/editor mutation on the GUI thread. Do not start another application
    event loop. Do not retain borrowed events or painters after callbacks.
16. Save or overwrite only within the authorized scope. Inspect the exact save
    API and format. Closing, exporting, and saving a copy have different effects.
17. Stop after errors. Report any completed partial edits. Never claim rollback,
    Undo support, atomicity, successful saving, or successful execution without
    evidence. A print statement or a truthy wrapper is not sufficient evidence.
18. Return bounded diagnostics: targets, changes, skipped items, failures,
    verification, and output paths. State what was inspected versus changed.
```

## 2 Resolve the runtime and API contract

### 2.1 Environment rules

- **ENV01 MUST:** Execute FontLab model access inside FontLab's initialized Python environment. A system Python interpreter is appropriate for pure text, JSON, mathematics, and file-processing helpers, but does not automatically control FontLab.
- **ENV02 MUST:** Check the Python major version and required modules. Do not assume a specific Python 3 minor version from the product name.
- **ENV03 SHOULD:** Use the standard library unless the task needs a verified installed dependency. Do not install or upgrade libraries in the embedded interpreter as an incidental part of a font edit.
- **ENV04 MUST:** Keep script entry points in functions. Do not clear shared globals, replace application modules, terminate the process, or call `sys.exit()` to finish an ordinary embedded script.
- **ENV05 MUST:** Treat font notes, glyph names, JSON, help results, and imported files as data. Do not execute their contents through `eval`, `exec`, or shell interpolation.

A bounded, read-only environment probe:

```python
import sys
import fontlab as fl

if sys.version_info.major != 3:
    raise RuntimeError("This script requires Python 3")

print({
    "python": sys.version.split()[0],
    "has_current_font": fl.CurrentFont() is not None,
    "has_editor_package_api": hasattr(fl, "flPackage"),
})
```

`hasattr` proves only that a name is exposed. It does not establish its signature, side effects, or suitability. `inspect.signature()` is not reliable for every native or PythonQt wrapper; use the installed documentation and binding definition when necessary. Do not execute a mutating overload just to discover its signature.

### 2.2 Evidence order

For a specific installation, use this order:

1. The installed runtime's actual capabilities and installed tool schemas.
2. Documentation matching that installation and Python binding definitions matching that build.
3. Regression examples for the same binding and object type.
4. Generated reference catalogs, after checking their scope and freshness.
5. Older examples or third-party wrappers, treated as unverified until reconciled.

A generated catalog can omit a method, truncate a description, or retain an old signature. Its absence is not proof of absence from the application; its presence is not proof of compatibility with every FontLab 9 release. When reliable evidence is unavailable, describe the missing API information and leave the dependent operation unresolved instead of fabricating code.

Do not assume TypeRig, RoboFab-compatible wrappers, or any other optional layer is installed. If a project requires one, identify it and keep its API separate from the native APIs below.

## 3 Keep the object models separate

| Object or module | Meaning | Correct use |
|---|---|---|
| `fontlab` | Editor integration and `fl*` model classes | Editor layers, elements, notifications, UI integration |
| `fontgate` | `fg*` font data model | FontGate structures, pens and low-level font data |
| `fl.CurrentFont()` | Current `fgFont`, or no font | Capture the user's current font once |
| `fl.CurrentGlyph()` | Current `fgGlyph`, or no glyph | Resolve an active glyph; do not assume it is an `flGlyph` |
| `fl.flPackage(fg_font)` | Editor wrapper for the font | Find editor glyphs and inspect master context |
| `package.findName(name)` | Editor `flGlyph`, or a missing result | Target an exact glyph without changing selection |
| `glyph.findLayer(name)` | Existing editor layer | Read or edit an explicit existing layer |
| `glyph.findLayerCreate(name)` | Lookup with possible creation | Use only when creation is intended |
| `flShape` | Element instance | Holds placement, paint, and geometry/builder references |
| `flContour` and `flNode` | Native editor outlines | Traverse and edit native outline data |
| `PythonQt` | The application's Qt bridge | Use the application's Qt types and object lifetimes |
| `fontpr` | In-process access to available MCP tools | Call native tool contracts from embedded Python |
| VFJ JSON | Serialized data | Read and write using the VFJ contract; not a live object API |

The practical hierarchy for ordinary editor geometry is:

```text
fgFont -> flPackage -> flGlyph -> flLayer -> flShape -> flContour -> flNode
                                        -> anchors
                                        -> guidelines and hints
```

A shape can instead be a component, group, live builder, image, or sticker. The hierarchy does not imply that every shape has independently editable outline contours.

### 3.1 Properties and methods

Use the Python binding's exposed form, not the C++ spelling or a remembered form from another class.

| Expression | Form | Common mistake |
|---|---|---|
| `fg_font.glyphs` | Property | Calling `fg_font.glyphs()` |
| `glyph.layers` | Property | Calling `glyph.layers()` |
| `glyph.activeLayer` | Property | Treating the active layer as an explicit master target |
| `layer.shapes` | Property | Appending to the returned list instead of calling `layer.addShape` |
| `shape.contours` | Property | Calling `shape.contours()` |
| `contour.nodes()` | Method | Iterating the method object `contour.nodes` |
| `node.x`, `node.y` | Properties | Assigning through a nonexistent `node.position.x` path |
| `layer.advanceWidth` | Property | Inventing `setWidth` or using another model's `width` |
| `shape.transform` | Property | Assuming the same representation as `fgMatrix` or a VFJ object |
| `shape.isComponent`, `shape.isComposite` | Properties | Calling the boolean as a method |
| `glyph.inkBox()` | Method | Calling it on a FontGate glyph without confirming that API |
| `contour.boundingBox()` | Method | Assuming every object's bounds member has the same form |
| `fontpr.available()` | Method | Testing the function object as a boolean |

Lists returned by bindings can contain live native wrappers while the list itself is a snapshot. Mutating a contained node may change the font; appending to the Python list may not change native membership. Use documented add/remove operations or a documented property setter to change membership.

Constructors and `clone()` operations have class-specific copy behavior. Do not assume `list(...)`, a copy constructor, or `copy.deepcopy()` creates an independent native object graph. Preserve identity unless detachment is part of the task.

## 4 Target the intended data explicitly

- **TARGET01 MUST:** Resolve the font, exact glyph names, and exact layer names before mutation.
- **TARGET02 MUST:** Distinguish active glyph, selected glyphs, and all glyphs. An active glyph is not evidence of the full selection.
- **TARGET03 MUST:** Reject missing targets unless the request includes creation. Never turn an inspection into `findLayerCreate`.
- **TARGET04 SHOULD:** Pass the selected package explicitly to helpers. Do not repeatedly call `CurrentFont()` inside a long loop and accidentally follow changes in application focus.
- **TARGET05 MUST:** Revalidate targets after any operation that replaces data or yields control to a callback. Native IDs are session identifiers, not durable identifiers across reopen.

A reusable resolver:

```python
import fontlab as fl


def require_current_package():
    fg_font = fl.CurrentFont()
    if fg_font is None:
        raise RuntimeError("Open the intended font before running this script")
    package = fl.flPackage(fg_font)
    if not package:
        raise RuntimeError("The current font has no usable editor package")
    return package


def require_glyph_layer(package, glyph_name, layer_name):
    if not glyph_name or not layer_name:
        raise ValueError("Exact glyph and layer names are required")
    glyph = package.findName(glyph_name)
    if not glyph:
        raise ValueError("Glyph not found: {!r}".format(glyph_name))
    layer = glyph.findLayer(layer_name)
    if not layer:
        raise ValueError("Layer {!r} missing in {!r}".format(layer_name, glyph_name))
    return glyph, layer
```

These functions do not create objects or change the active document. Their use of the current font is an explicit policy choice; a multi-font task should resolve its package from a verified font list instead.

For batch scripts, materialize the requested glyph-name list before editing. If names come from selection, document how the installed selection API defines that selection. Deduplicate names without reordering them. Do not silently substitute descriptive aliases for exact native names.

## 5 Separate preview from execution

Use this sequence:

1. Parse configuration and resolve the target package.
2. Read all targets, constraints, and relevant geometry.
3. Validate names, finite numeric values, layer policy, and required methods.
4. Calculate proposed edits without assigning to native objects.
5. Return or print a bounded preview.
6. If execution is authorized, establish the appropriate history scope and apply edits.
7. Notify changes and reacquire affected data where needed.
8. Verify requested results and preservation of unrelated data.
9. Save only if requested, and report the actual output path and save result.

A script's `dry_run` flag must actually prevent all writes. Calling a setter and then Undo is not a read-only preview. Avoid history notifications, selection changes, layer creation, preference changes, and file writes in preview mode.

State whether the edit is idempotent. Setting a width to an absolute value is ordinarily repeatable without cumulative movement; adding 20 units repeatedly is cumulative. Creating an anchor or component can create duplicates unless the script has an explicit identity policy. Never automatically replay a partially completed destructive operation after a timeout or exception.

For large edits, validate all predictable failures before changing the first glyph. If a native error occurs mid-batch, stop, identify completed targets, and keep the application consistent enough for inspection. Python exceptions do not automatically undo native mutations.

## 6 History, cache refresh, redraw, and saving

These are distinct responsibilities:

| Responsibility | Meaning |
|---|---|
| Mutation | Change native data |
| Cache refresh | Make derived bounds and geometry consistent with edited data |
| History enrollment | Record changes in the correct owning package for Undo/Redo |
| Redraw | Request a visual refresh |
| Save | Write a font or exported artifact to disk |

For direct edits to existing editor layers and glyphs, the scoped pattern used by the current bindings and regressions is:

```python
# Fragment: glyph and layer must already be resolved and all edits validated.
import fontlab as fl

title = "Set explicit layer width"
fl.flItems.notifyChangesApplied(title, [layer, glyph])
layer.advanceWidth = 640.0
fl.flItems.notifyChangesApplied(title, [layer, glyph])
```

Use recursive history, which is the default in the current binding. Shallow history can fail to capture nested node geometry and contour ordering. Supplying actual objects also gives the notification path the scope needed to refresh owned geometry; the no-argument form does not walk arbitrary fonts to discover what changed.

This pattern is not a transaction, and its exact Undo grouping must be checked for the operation and build. It does not make arbitrary package-wide edits, preferences, file writes, or external actions undoable. Do not wrap an already undo-managed MCP operation in extra native notifications without a reason.

`glyph.update()`, `fl.Update(glyph)`, and canvas redraw calls are not interchangeable with the scoped history path. `AcceptChanges()` participates in change-controller processing and defaults to clearing changed-state bookkeeping; it is not a generic “make everything safe” command. Do not call it as a ritual at the end of every script.

When a mutation can raise after partial changes, arrange for scoped final notification if the owning objects still exist, while preserving and reporting the original exception. Do not claim that a `finally` notification rolled back anything. Avoid holding wrappers across operations that replace their owner.

### 6.1 An absolute width edit with a real preview

This self-contained example edits one explicitly named existing layer in the current font. It rejects automatic layers and metric expressions rather than silently overriding driven widths. It does not save or change the active master.

```python
import math
import fontlab as fl


def set_layer_widths(glyph_names, layer_name, width, dry_run=True):
    if isinstance(glyph_names, str):
        raise TypeError("glyph_names must be a sequence of exact names")
    if not isinstance(dry_run, bool):
        raise TypeError("dry_run must be a boolean")
    if isinstance(width, bool) or not isinstance(width, (int, float)):
        raise TypeError("width must be a number")
    width = float(width)
    if not math.isfinite(width) or not 0.0 <= width <= 100000.0:
        raise ValueError("This example accepts widths from 0 to 100000")
    if not isinstance(layer_name, str) or not layer_name:
        raise ValueError("An exact layer name is required")

    names = list(glyph_names)
    if not names or any(not isinstance(name, str) or not name for name in names):
        raise ValueError("Provide nonempty glyph names")
    names = list(dict.fromkeys(names))

    fg_font = fl.CurrentFont()
    if fg_font is None:
        raise RuntimeError("No current font")
    package = fl.flPackage(fg_font)
    plan = []
    for name in names:
        glyph = package.findName(name)
        if not glyph:
            raise ValueError("Glyph not found: " + name)
        layer = glyph.findLayer(layer_name)
        if not layer:
            raise ValueError("Missing layer {} in {}".format(layer_name, name))
        if layer.autoLayer:
            raise ValueError("Automatic layer requires a different policy: " + name)
        if layer.isLockedI:
            raise ValueError("Locked layer: " + name)
        if layer.metricsWidth or glyph.metricsWidth:
            raise ValueError("Width expression must be handled explicitly: " + name)
        old_width = float(layer.advanceWidth)
        if old_width != width:
            plan.append({"glyph": name, "before": old_width, "after": width})

    report = {"dry_run": dry_run, "layer": layer_name, "planned": plan,
              "completed": [], "saved": False}
    if dry_run:
        return report

    for item in plan:
        # Reacquire; do not depend on wrappers collected during planning.
        glyph = package.findName(item["glyph"])
        layer = glyph.findLayer(layer_name) if glyph else None
        if not layer or float(layer.advanceWidth) != item["before"]:
            raise RuntimeError("Target changed since planning: " + item["glyph"])
        title = "Set width of " + item["glyph"]
        fl.flItems.notifyChangesApplied(title, [layer, glyph])
        try:
            layer.advanceWidth = item["after"]
        finally:
            # This records/refreshes a possible partial edit; it is not rollback.
            fl.flItems.notifyChangesApplied(title, [layer, glyph])
        actual = float(package.findName(item["glyph"]).findLayer(layer_name).advanceWidth)
        if actual != item["after"]:
            raise RuntimeError("Width readback differs for " + item["glyph"])
        report["completed"].append(item["glyph"])
        print("Verified width:", item["glyph"], actual)
    return report


if __name__ == "__main__":
    # Edit these configuration values for the intended project.
    print(set_layer_widths(["A", "B"], "Regular", 640.0, dry_run=True))
```

The accepted width range above is a policy of this example. It is not a claim that negative widths are universally invalid. If a later target fails, earlier completed targets remain edited; their verification lines identify them. For production batch tools, preserve a structured failure report containing both completed targets and the failed target.

## 7 Outline geometry and coordinate spaces

### 7.1 Read outline data deliberately

A read-only inspection using the resolver functions from section 4:

```python
package = require_current_package()
glyph, layer = require_glyph_layer(package, "A", "Regular")

rows = []
for shape_index, shape in enumerate(layer.shapes):
    if shape.isComponent or shape.isComposite:
        rows.append({"shape": shape_index, "kind": "component_or_composite"})
        continue
    for contour_index, contour in enumerate(shape.contours):
        rows.append({
            "shape": shape_index,
            "contour": contour_index,
            "closed": bool(contour.closed),
            "node_count": len(contour.nodes()),
        })
print(rows[:50])
```

This does not claim to count nested or component-source contours. It intentionally reports their presence rather than silently decomposing them.

- **GEOM01 MUST:** Distinguish shape-local coordinates, contour transforms where present, layer coordinates, and canvas coordinates. A node's `x` and `y` do not necessarily equal its visible layer position.
- **GEOM02 MUST:** For a position change in layer coordinates, use a verified transform conversion or change the element's placement. Do not apply a layer-space displacement directly to local nodes under an arbitrary transform.
- **GEOM03 MUST:** Do not edit a component source to move one component instance. Do not detach shared data unless authorized.
- **GEOM04 MUST:** Maintain curve topology, closure, start point, node names, and required handles. A contour is not just a list of independent on-curve points.
- **GEOM05 SHOULD:** Snapshot index targets before changing membership. Delete original indices in descending order, or explicitly recompute indices after each edit.
- **GEOM06 MUST:** Reject non-finite coordinates. Choose rounding and tolerances based on the operation and file format; do not assume all font coordinates are integers.

For native `flNode`/`nodes_list` terminology, `on` is an on-curve endpoint, `curve` is an ordinary cubic control point, and `off` is a quadratic control point. A cubic segment normally has two control points between endpoints. Quadratic off-curve chains can imply intermediate points. Do not transplant these spellings or numeric enums into FontGate constructors without checking that API.

A native contour can be built as follows. This is an in-memory construction fragment; it does not attach the shape to a font or provide an Undo step:

```python
import fontlab as fl
from PythonQt import QtCore

nodes = [fl.flNode(QtCore.QPointF(x, y), nodeType="on")
         for x, y in ((50, 0), (550, 0), (550, 700), (50, 700))]
contour = fl.flContour(nodes, closed=True)
shape = fl.flShape()
shape.addContour(contour, True)
```

Attach it to a resolved layer using `layer.addShape(shape)` inside the verified mutation workflow. Appending `shape` to a temporary Python list of shapes is not equivalent.

### 7.2 Matrices

For `PythonQt.QtGui.QTransform(a, b, c, d, tx, ty)`:

```text
x_new = a*x + c*y + tx
y_new = b*x + d*y + ty
```

A component or element's `transform` property uses a Qt transform. Construct and assign a complete transform when replacing placement:

```python
from PythonQt import QtGui

# Fragment: the target shape is already inspected and its owner is in history scope.
shape.transform = QtGui.QTransform(1.0, 0.0, 0.0, 1.0, 30.0, 10.0)
```

This replaces the previous transform; it does not merely add translation. Preserve existing scale, rotation, reflection, and shear when the request is only an offset change. Verify matrix multiplication order with a known point before composing transforms. Do not assume `fgMatrix`, Qt transforms, and JSON transform objects share constructor order or representation.

Negative scale reflects geometry and can reverse winding. Scaling outlines does not automatically define whether advance widths, anchors, guidelines, hints, or other masters should also change. Specify those decisions before applying a transform.

### 7.3 Bounds and measurement

Bounds may describe stored geometry, rendered ink, or export-prepared contours. Pick the appropriate method and object type. Cached bounds can be stale after low-level mutations until the scoped notification/update path refreshes owners.

Font coordinates normally increase upward in y. `QRectF.top()` and `bottom()` follow numeric rectangle conventions, not the visual meaning of “top of a glyph.” Derive `y_min` and `y_max` explicitly and explain which one is used. Treat empty bounds separately. Do not approximate rendered extrema by taking the maximum control-point coordinate of a Bézier curve.

## 8 Components, groups, anchors, and hints

### 8.1 Component creation and placement

The current `flLayer.addComponent` binding accepts a source name or a **single tuple** containing the source name and Qt transform. It creates a live component shape, checks that the source exists in the layer's font, and rejects invalid/cyclic component construction. The binding returns `None`; do not use its return value as the newly added shape.

```python
# Fragment: existing source H, resolved target glyph/layer, non-Auto destination.
import fontlab as fl
from PythonQt import QtGui

title = "Add H component"
fl.flItems.notifyChangesApplied(title, [layer, glyph])
layer.addComponent(("H", QtGui.QTransform(1, 0, 0, 1, 30, 10)))
fl.flItems.notifyChangesApplied(title, [layer, glyph])
```

Do not repeat this fragment blindly: it adds another component each time. Establish a duplicate policy and verify the destination layer and source layer. This API uses the destination layer name for the source builder; cross-layer source selection requires a separately verified API or a schema-backed VFJ edit.

`setGlyphComponents(components, width, package, colorize, flags=0)` replaces shape content; it is not an append operation. Its legacy tuple form uses `(name_id, transform, width_scale, use_anchors)`, which is different from the tuple accepted by `addComponent`. `package.generateGlyph(...)` returns component data, not a guaranteed `(components, width)` pair. Use the actual binding signature and validate the return before destructuring.

Live groups and automatic builders can regenerate derived contours. Modify their defining inputs when that is the requested operation. Do not treat generated output as independent permanent geometry.

### 8.2 Anchors

Use `flPinPoint` for editor anchors and the layer's explicit anchor API. The native `point` is a `QPointF`; writable VFJ represents it differently. An existing anchor can have expressions, cloud positioning, mark behavior, and shape binding. Preserve those states or explicitly explain a requested detachment.

Adding an anchor with an existing name requires a policy: update that anchor, reject the duplicate, or intentionally create a distinct record. Never silently append duplicates to make a setter work.

Fractional anchor values are supported, but the editor's strong-rounding preference can affect setter results. Do not change a global preference silently. Read back coordinates; if precision is essential, use an authorized scoped preference change with restoration in `finally`, and verify it on the target build.

### 8.3 Hints and guidelines

Do not confuse detected stems, PostScript hint records, TrueType instructions, and guidelines. They use different APIs and semantics. A hint can be driven by linked nodes or expressions; changing its stored position may not move the effective hint as expected.

If available, `get_layer_hints` and `edit_layer_hints` provide focused, undo-managed PostScript hint edits through MCP or `fontpr`. Discover their current schemas, inspect links, and use explicit detachment only when requested. Do not assume these tools edit TrueType instructions.

## 9 Fonts with multiple masters and variable data

- **MASTER01 MUST:** Identify the exact target layer or master and whether the task covers one, several, or all masters.
- **MASTER02 MUST:** Preserve unrelated layers, masks, service layers, bracket data, axis locations, and interpolation metadata.
- **MASTER03 MUST:** Before structural edits across compatible masters, compare contour count, contour order, start points, node kinds, and component order. Matching node counts alone does not prove compatibility.
- **MASTER04 MUST:** Do not rename or reorder masters merely to simplify lookup.
- **MASTER05 MUST:** If an API operates through the active master, capture and restore the original master using a verified API. Prefer APIs with an explicit target parameter.
- **MASTER06 MUST:** Keep metrics, anchors, hints, kerning, and component source selection in their correct master context.

A layer name is not automatically a design-space coordinate. A glyph's active layer need not be the intended master. Preserve Sigma and other variable-data dictionaries during unrelated serialization edits; they can encode point identities and master relationships that a geometry-only rebuild would lose.

## 10 FontGate operations and ownership

Use FontGate when its specific data model and operation fit the task. Do not switch between `fg*` and `fl*` writes mid-operation without a verified synchronization and history strategy.

The current `flPackage.addGlyph(fgGlyph)` binding copies the argument into font ownership. Reacquire the inserted glyph with `package.findName(name)` before editing the editor model. This behavior was repaired in the source history; do not assume an older application is safe merely because the method exists.

Creation is a distinct operation from editing an existing glyph. Check for collisions before adding a glyph. Do not rely on constructor calls, object garbage collection, or Python reference counts to establish native font ownership or Undo behavior.

Python references can outlive their native targets. After a glyph replacement, close/reopen, deletion, or Undo/Redo, resolve fresh wrappers. Shared shape data can have owners outside the current glyph; copying the wrapper does not prove the source data is independent.

Changing encodings or names can affect lookup caches and mappings. Verify both the stored value and lookup behavior. Do not assume a repaint rebuilds lookup maps. Use a verified high-level mutation path where possible, especially for operations that affect multiple representations.

### 10.1 Names and Unicode encodings

A glyph name, Unicode scalar, glyph-list index, native object ID, and component source name are different identifiers. Do not use one in place of another. A glyph can be unencoded, have multiple Unicode values, or represent a character sequence rather than one character.

Use the encoding APIs documented for the actual object type. VFJ's single `unicode` value is hexadecimal text such as `"0041"`, whereas its `unicodes` array contains integer code points. Do not apply that serialized convention to a Python property without checking its contract. Preserve non-BMP values and additional encodings; do not reduce a glyph's encodings to its first value unless requested.

After an encoding or name change, verify both the object and the relevant name/Unicode lookup. If an operation can invalidate a lookup cache, use the high-level path that manages that invalidation. Rebuilding arbitrary font caches should not be a substitute for understanding ownership and notification.

### 10.2 Kerning and font metadata

Kerning is master-sensitive and can involve glyph pairs, classes, class membership, and exceptions. A numeric pair value alone does not describe the full kerning behavior. Resolve both sides and the intended master; preserve class assignments and exceptions unless the user asks to change them.

For MCP kerning operations, discover the available tool schemas and class naming convention instead of assuming a dictionary layout. A zero value and a deleted pair can have different effects when a class pair is inherited. Check the requested effective behavior after the edit.

Font metadata may live at font, master, instance, or glyph scope. Family names, style names, name-table values, export settings, and glyph metrics are not interchangeable. Determine the field's scope and read/write status before assigning it. Do not rewrite a whole metadata dictionary just to change one known field if a focused setter exists.

## 11 Calling MCP tools from Python

`fontpr` is optional and depends on a ready MCP-enabled application. It exposes the same native tool contracts available through MCP; it is not an independent font object model.

```python
import fontpr

if not fontpr.available():
    raise RuntimeError("FontLab MCP tools are not ready")

tools = {entry["name"]: entry for entry in fontpr.list_tools()}
if "get_glyph" not in tools:
    raise RuntimeError("This build does not advertise get_glyph")

# Fragment: package is the explicitly selected flPackage.
data = fontpr.call("get_glyph", font_id=int(package.fgId), glyph_name="A")
```

Use keyword arguments for tool parameters. The positional argument to `fontpr.call` is the tool name; dynamic convenience calls also require their tool parameters as keywords. Do not pass a parameter dictionary as an extra positional argument and assume it will be consumed.

Successful tool results are decoded into Python values. An MCP error raises `fontpr.Error`. Do not keep editing after catching that exception unless recovery is explicitly designed. Some numeric values arrive as Python floats through the JSON bridge; validate that an index is integral before converting it to `int`.

`run_python` and `get_python_output` are intentionally unavailable through `fontpr`. Do not recursively invoke Python execution through its own tool bridge. Do not bypass a chatbot's Python execution authorization by choosing a different entry point.

When a focused tool fully handles the edit, prefer its validation, master targeting, and Undo semantics over hand-reimplementing those behaviors. Inspect the advertised schema first; arguments and capability sets can change between builds.

### 11.1 Editing writable VFJ

For a whole-glyph edit, follow this contract:

1. Discover `get_glyph`, `set_glyph`, and optional `get_vfj_schema`/`dry_run` support.
2. Fetch full `get_glyph` output. Do not request `detail="construction"` as the edit base.
3. Read the relevant VFJ topic if schema discovery is available.
4. Modify only the intended dictionary path and preserve unrelated fields.
5. Validate using `set_glyph(dry_run=True)` if advertised.
6. Commit only the validated intended payload, then reacquire and verify.

`set_glyph` replaces the whole glyph. It is not a JSON merge operation or a layer patch. Sending only the edited layer can remove other layers. A Python dictionary is required by the advertised API; do not send `json.dumps(data)` as `glyph_data`.

Representative writable VFJ paths:

```text
layers[].elements[].elementData.contours[].nodes_list[]
layers[].anchors[]
layers[].elements[].component.glyphName
layers[].elements[].transform
```

An ordinary VFJ element transform is an object with fields such as `xScale`, `xyScale`, `yxScale`, `yScale`, `xOffset`, and `yOffset`. It belongs beside `component`, not inside it. Construction summaries and some specialized builder dictionaries use other representations; consult the exact schema instead of globally converting every field named `transform`.

The recent schema-enabled implementation validates structure and detached native parsing, preserves additional glyph metadata, and embeds PNG bytes for portable replacement. Successful dry-run validation does not establish component dependency correctness, expression results, or visual correctness. Discover availability instead of assuming that every released FontLab 9 build has these features.

Do not reconstruct a full glyph from truncated JSON. The recent chat implementation permits `glyph_data` up to 262144 UTF-16 code units and preserves glyph/schema reads up to 524288 units. Those are host chat limits, not font-format limits or universal Python limits. A script calling the native bridge directly is not subject to that particular chat argument check.

## 12 Files, saving, and closing

- **FILE01 MUST:** Use explicit paths and check the intended format. Do not overwrite a source font or export unless the user's task authorizes it.
- **FILE02 MUST:** Distinguish native save, save-copy, and export. A file extension does not turn an arbitrary low-level save API into a native FontLab save.
- **FILE03 MUST:** Verify the actual save result and output path. Existence alone does not prove that every intended change was serialized.
- **FILE04 SHOULD:** Use UTF-8 explicitly for text and JSON. Use binary mode for bytes. Avoid relying on the process working directory.
- **FILE05 MUST:** Preserve encoding values, glyph names, notes, and unrelated metadata exactly unless normalization is requested.

A current binding trap: `flPackage.close(prompt=True)` controls whether to prompt. `close(False)` can discard unsaved changes without prompting; it is not a request to save. Older generated references may describe this parameter incorrectly. Inspect the installed binding before closing anything.

Likewise, a FontGate `save` method can have a different format contract from FontLab's native document save. If available, the MCP `save_font` tool provides an explicit native-format contract. Read its current schema, including copy semantics, overwrite policy, and dirty-state behavior. Preferences and file writes are outside ordinary glyph Undo.

For a save-sensitive operation, verification should include reopening the generated copy in an isolated workflow and checking representative geometry and metadata. Do not close the user's source document just to perform that test.

## 13 Qt and interactive scripts

Use the application's `PythonQt` bridge. Do not mix native QObject wrappers with PyQt/PySide wrappers in the same UI object graph unless a documented integration explicitly supports that arrangement.

- **UI01 MUST:** Perform editor mutations and UI work on the GUI thread. Background work should operate on independent plain Python data and return results for application on the GUI thread.
- **UI02 MUST:** Reuse the existing application and event loop. Do not construct another `QApplication` or call its main event loop from an ordinary script.
- **UI03 MUST:** Keep callbacks short. Do not mutate a font from a paint callback or block event handling with long loops or network requests.
- **UI04 MUST:** Treat borrowed painters and event wrappers as valid only during the callback. Copy primitive values needed later; do not retain native pointers for deferred use.
- **UI05 MUST:** Store registration tokens and unregister painters, tools, timers, and callbacks during cleanup or reload.
- **UI06 SHOULD:** Keep Python-owned UI/controller references alive for their intended lifetime, while respecting Qt parent ownership. Do not manually destroy arbitrary native widgets.

Newer builds expose `canvas.appendPythonPainter`, `removePythonPainter`, and workspace Python tool registration. Check those capabilities before use. Canvas painting coordinates are viewport coordinates; font coordinates require a documented mapping. Do not assume a signal overload, enum type, Qt module location, or keyword-overload behavior from another Python Qt binding.

For expensive operations, process bounded work units and support cancellation at safe boundaries. Reentering the event loop with `processEvents()` can allow document changes during the operation; it is not a substitute for a deliberate asynchronous design.

## 14 Debugging and verification

Classify failures before changing code:

| Symptom | First checks |
|---|---|
| `AttributeError` | Exact object class, API availability, property versus method, stale generated reference |
| `TypeError` from a native wrapper | Argument count, keyword support, overload types, tuple shape, enum type |
| No visible change | Wrong font/layer, derived geometry, cache/notification path, failed setter, locked or automatic layer |
| Unexpected movement | Local versus layer coordinates, matrix order, shared sources, automatic attachment |
| Undo misses geometry | Wrong object scope, missing baseline/final notification, shallow history, unsupported operation |
| Missing data after JSON write | Whole-glyph replacement, omitted layers/fields, wrong VFJ nesting, unresolved references |
| Exception partway through a batch | Completed targets, retry policy, partial edits; do not assume rollback |
| Native crash or hang | Invalid lifetime, malformed native data, reentrant callback, unsupported API; stop retries and isolate a minimal reproducer |

Verify the postconditions that matter to the user:

- Exact target font and layers changed.
- Requested values or geometry are present on readback.
- Unrelated layers, outlines, anchors, components, metrics, encodings, and metadata remain intact.
- Shared sources and dependent components behave as intended.
- Undo and Redo restore representative before/after states when that support is claimed.
- Re-running an idempotent script does not accumulate changes.
- Saved output can be reopened when file correctness is part of the task.

Choose numerical comparisons deliberately. Use exact equality for discrete identifiers, names, counts, and exact integer operations. For floating calculations or serialized binary coordinates, use a justified tolerance tied to precision; do not use a loose tolerance to hide unexpected normalization.

Use bounded diagnostic output. Avoid printing an entire font, every node, or full embedded image data when a count, a few examples, or a JSON path is sufficient. Preserve tracebacks for failures and do not replace them with a success message.

A useful result structure is:

```json
{
  "status": "preview",
  "target": {"font": "explicitly resolved font", "layers": ["Regular"]},
  "planned_count": 2,
  "completed_count": 0,
  "skipped": [],
  "failures": [],
  "verification": "No writes performed",
  "saved_paths": []
}
```

For real execution, use a status that reflects completed or partial work. Do not emit `status="ok"` after catching an unhandled edit failure. Report which checks were actually performed; do not claim a visual inspection from a numeric readback alone.

## 15 Incorrect patterns and preferred corrections

| Incorrect pattern | Preferred correction |
|---|---|
| Guess `font.updateGlyph(name)` | Verify the owning model and use its documented notification/update path |
| Call `CurrentFont().glyphs()` | Inspect `CurrentFont().glyphs` as the FontGate property |
| Call `inkBox()` on every object returned by a font's glyph list | Resolve an editor `flGlyph` through `flPackage` when using that API |
| Use `layer.shapes.append(shape)` and assume native insertion | Use `layer.addShape(shape)` |
| Iterate `contour.nodes` | Call `contour.nodes()` for native editor contours |
| Use `findLayerCreate` during a read-only report | Use `findLayer` and report missing layers |
| Use `layer.addComponent("A", matrix)` | Use the verified single argument `layer.addComponent(("A", matrix))` |
| Treat `addComponent`'s result as a shape | Reinspect the layer; that binding returns `None` |
| Call `setGlyphComponents` to append one component | Recognize its replacement semantics; choose an append API |
| Call `fl.Update` and promise Undo | Use and test the correct history workflow separately |
| Treat `close(False)` as a save | Check its prompt/discard semantics before calling |
| Reuse wrappers after `set_glyph` or Undo | Reacquire by explicit package, glyph name, and layer name |
| Apply a translation matrix that erases an existing scale | Preserve and compose transforms in a verified order |
| Put `transform` inside a VFJ `component` | Put it on the enclosing ordinary element |
| Pass a construction summary to `set_glyph` | Fetch full writable VFJ |
| Catch all errors, print “done,” and continue | Stop, retain the traceback, and report partial results |
| Install a random Python package to repair an API mismatch | Verify the embedded runtime and installed binding first |

## 16 Use for training and evaluation

Use this guide as instruction/context material, or as the policy basis for supervised examples. It is not itself a provider-specific fine-tuning upload file. Convert it into the training format required by the chosen training system only when that is requested.

For training examples:

1. Pair a concrete user request with the relevant runtime/version context and API evidence.
2. Show the correct distinction between explanation, script generation, preview, and execution.
3. Prefer small examples that teach one decision: target resolution, property syntax, Undo scope, coordinate space, or save semantics.
4. Include missing fonts/layers, unsupported methods, stale wrappers, and partial failures as ordinary cases.
5. Label incorrect code explicitly. Never present a bad example without its correction and reason.
6. Keep capability-dependent behavior conditional. Do not train a newly added method as universally available in every build.
7. Use synthetic fonts and nonsensitive metadata. Do not include private font outlines, credentials, or local user paths without authorization.
8. Do not label unexecuted code as tested. Keep evidence labels such as “syntax checked,” “source verified,” “isolated runtime tested,” and “verified in target application” distinct.

Suggested evaluation scenarios:

| Scenario | Required behavior |
|---|---|
| No font is open | Clear error; no implicit font creation |
| Requested layer is absent | Report it; no silent creation or fallback |
| Batch contains one invalid target | Detect before writing when predictable |
| Width is driven by an expression | Preserve it or apply an explicitly requested override policy |
| Selected shape is a component | Edit the instance or explain source-edit consequences |
| Two elements share shape data | Detect/preserve shared ownership; avoid unintended source edits |
| Matrix contains a shear and translation | Preserve coefficients and verify mapped points |
| JSON contains only one layer of a multi-master glyph | Refuse to treat it as a partial patch |
| A dry run is requested | No font, UI, history, preference, or filesystem mutation |
| An exception occurs after the first glyph | Report the first edit and stop; no false rollback claim |
| User asks to save a copy | Correct format/path and overwrite behavior; no source close |
| Existing project uses an older binding | Discover supported behavior; no invented compatibility fallback |

Reject an answer that invents an API, silently changes scope, confuses object models, or claims unverified execution—even if its prose sounds plausible.

## 17 Reference map and maintenance

Use these repository references for lookup and build-specific verification:

| Reference | Purpose |
|---|---|
| [Full Python API catalog](fontlab_python_api.json) | Searchable generated API definitions; verify freshness |
| [Compact API catalog](fontlab_python_api_chat.json) | Small retrieval-oriented subset, not an exhaustive authority |
| [Full text API reference](fontlab_python_api.llm.md) | Method/property lookup |
| [Python and MCP overview](../docs/SETUP.md) | Existing reference-generation workflow |
| [Python module integration](../docs/PROVENANCE.md#source-references) | CurrentFont, CurrentGlyph, Update, AcceptChanges |
| [Package bindings](../docs/PROVENANCE.md#source-references) | Package construction, glyph insertion, master operations, close semantics |
| [Glyph bindings](../docs/PROVENANCE.md#source-references) | Editor glyph properties and layer lookup |
| [Layer bindings](../docs/PROVENANCE.md#source-references) | Layer properties, components and shape insertion |
| [Shape bindings](../docs/PROVENANCE.md#source-references) | Element geometry and transforms |
| [Contour bindings](../docs/PROVENANCE.md#source-references) | Node access, construction and contour operations |
| [Notification bindings](../docs/PROVENANCE.md#source-references) | Scoped notifications and recursive history |
| [Python MCP bridge](../docs/PROVENANCE.md#source-references) | Availability, keyword calls, result conversion and errors |
| [MCP guide](../docs/mcp/GUIDE.md) | Current native tool contracts |
| [VFJ schema catalog](vfj_schema.json) | Writable serialization structure in schema-enabled builds |
| [VFJ schema reference](../docs/mcp/VFJ.md) | Detailed generated schema documentation |
| [Scripting API fixes](../docs/PROVENANCE.md#source-references) | Build-dependent history, components, Qt and rounding changes |
| [Scripting lifetime fixes](../docs/PROVENANCE.md#source-references) | Ownership and callback lifetime constraints |
| [Native Python regression examples](../docs/PROVENANCE.md#source-references) | Components, geometry and Undo patterns; fixtures injected by a test host |
| [Geometry and metadata regressions](../docs/PROVENANCE.md#source-references) | Bounds refresh, shared ownership and metadata behavior |
| [Glyph ownership regression](../docs/PROVENANCE.md#source-references) | Inserted FontGate glyph ownership and editor reacquisition |

When APIs change, update this guide from the binding and its regression evidence. Do not hand-edit generated API catalogs to disguise a mismatch; update their generator/source and regenerate them separately. Keep the compact instruction block consistent with the detailed rules, and record version-sensitive behavior next to the relevant operation.

# AEC Modeling USD Conventions (MVP)

This document freezes the MVP USD layout used by My Own Software before the next pipeline stage.

## Global Rules

- Stage up axis is Z and units are meters (`stageMetersPerUnit=1.0`).
- Generated building data lives under `/World/Building`.
- Geometry that exists only to support rebuilds may be hidden, but should remain in USD if it is the source of bounds or metadata.
- Parametric intent is stored as simple `aec:*` attributes and relationships on USD prims.
- Manual edits should be preserved only when the rebuild engine can convert them back into specs.

## Building Layout

```text
/World
  /Building                         Xform, aec:type=Building, aec:schemaVersion=mvp-1
    /Sketches                       Xform, global sketch container
    /Block_01                       Xform, aec:type=Block
      /Sketch                       Xform, block sketch container
      /Mass                         Xform, hidden technical mass container
        /BlockMesh                  Mesh, hidden, extruded block bounds
        /PrimitiveMesh              Mesh, hidden, primitive block bounds
      /Spaces                       Xform
        /Space_01                   Xform, aec:type=Space
          /Surfaces                 Xform
            /Floor                  Mesh, aec:type=Surface
            /Ceiling                Mesh, aec:type=Surface
            /Wall_XMin              Mesh, aec:type=Surface
            /Wall_XMax              Mesh, aec:type=Surface
            /Wall_YMin              Mesh, aec:type=Surface
            /Wall_YMax              Mesh, aec:type=Surface
      /Partitions                   Xform, generated partition meshes
      /Metadata                     Xform
      /_AEC                         Xform, persistent parametric intent
        /PartitionSpecs             Xform
        /OpeningSpecs               Xform
```

## Blocks

- `aec:type = "Block"`.
- `aec:blockKind = "Extruded"` or `"Primitive"`.
- Extruded blocks must have `aec:sourceCurveRel` pointing to a closed `UsdGeom.BasisCurves`.
- Primitive and extruded block mass meshes live under `Mass/` and are invisible by default.
- `Update Selected Block` regenerates mass, partitions, spaces, surfaces, and openings from current geometry plus specs.

## Spaces And Surfaces

- Spaces are generated under `Block_XX/Spaces/Space_XX`.
- Each space owns its own `Surfaces` container.
- Required MVP surfaces are `Floor`, `Ceiling`, `Wall_XMin`, `Wall_XMax`, `Wall_YMin`, and `Wall_YMax`.
- Exterior surfaces use `aec:outsideBoundaryCondition = "Outdoors"` or `"Ground"`.
- Internal matching surfaces use `aec:outsideBoundaryCondition = "Surface"` and adjacency relationships.
- Internal wall surfaces that coincide with generated partitions are hidden and marked `aec:hiddenByPartition = true`.
- Wall surfaces store stable basis attributes (`aec:basisOrigin`, `aec:basisHDir`, `aec:basisVDir`, `aec:basisWidth`, `aec:basisHeight`) so openings remain aligned after wall meshes are cut.

## Partitions

- Persistent intent lives in `Block_XX/_AEC/PartitionSpecs/PartitionSpec_XX`.
- Generated visible/editable partition meshes live in `Block_XX/Partitions/Partition_XX`.
- Partition specs store orientation, normalized offset, thickness, level, and generated mesh path.
- MVP partitions are full-height cut planes from floor to current block ceiling.
- If a generated partition mesh is deleted manually, `Update Selected Block` removes its spec and recalculates spaces without recreating it.

## Openings

- Persistent intent lives in `Block_XX/_AEC/OpeningSpecs/OpeningSpec_XX`.
- Generated openings live under their host surface:

```text
/Wall_XMin
  /Openings
    /Window_01
      /Panel
```

- Opening specs store opening type, width, height, sill/bottom height, horizontal offset, block relationship, and host surface relationship.
- Wall meshes are regenerated around opening rectangles so the opening replaces the wall area instead of only sitting on top.
- Opening panels are double-sided for viewport readability.

## Sketches

- Main building/block sketches live under `/World/Building/Sketches`.
- Opening sketches live under their host surface container when created from a selected wall.
- Sketches are `UsdGeom.BasisCurves` with linear type.
- Closed sketches use `wrap=periodic`; open line sketches use `wrap=nonperiodic`.
- Sketches can be drawn on selected surfaces, including upper floors/ceilings, not only at `Z=0`.

## MVP Check

The AEC Modelling `Check Model` button is the pre-next-stage gate. It should report issues for:

- Missing `/World/Building`.
- Blocks without mass mesh, spaces, or valid source sketch.
- Space count mismatch against partition specs.
- Spaces without required surfaces or bounds metadata.
- Surfaces without type, space relationship, or wall basis metadata.
- Partitions without valid specs or block relationship.
- Openings without valid host surface, spec, or panel mesh.
- Opening specs pointing to missing host surfaces or missing generated openings.
- Closed sketches that are not periodic or have fewer than three vertices.

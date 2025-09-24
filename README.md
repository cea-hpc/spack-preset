*spack preset* is a [spack](https://spack.readthedocs.io/en/latest/)
extension for creating cmake
[presets](https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html).
This spack command is an alternative to
[spack develop](https://spack.readthedocs.io/en/latest/command_index.html#spack-develop)
command for developping project/spack package using cmake as a build system.

Usage (with a spack spec)
-------------------------

Clone *spack preset* and declare it's path into spack
configuration `spack config --scope user add config:extensions:<path/to>/spack-preset`
(here configuration was modified at
[user scope level](https://spack.readthedocs.io/en/latest/configuration.html#configuration-scopes))

supposing your cmake project source are in `/cmake/project/sources` and
the spack package name for it is `project`:
```
cd /cmake/project/sources
spack preset project variant=value
```

create a `CMakeUserPresets.json` in project source directory
that can directly be used with your favorite IDE or with `cmake`

```
cmake --list-presets
cmake --preset <preset-name>
cmake --build --preset <preset-name>
```

As long as dependencies are not modified (e.g. spack instance),
recreating preset is not needed and you can focus on your project
development.

By default the name of the preset will be the spack hash for the
package, rather use the `--with-name`, `--with-display-name`
and `--with-description` of `spack preset` command.
Note that these flags understand the spack spec
[format string](https://spack.readthedocs.io/en/latest/package_api.html#spack.package.Spec.format)
(e.g '{name}-{version}-{architecture.target}')
 
`spack preset` do it's best to reproduce in the created preset the
spack environment used when actually installing the package.
Environment variables and cmake cached variables are copied verbatim
(compiler part is a bit more tricky because spack use wrapper for
compilers).

However you can override with -D flags the build behaviour not only
when you launch cmake but also when creating the preset (the
override will be saved in the preset in that case and not only
the `CMakeCache.txt` e.g. configure phase). Used when spack recipe
for project don't expose thru variants all the
options CMakeLists.txt provides (spack focus on deployment).

Usage (with a spack environment)
--------------------------------

`spack preset` can create multiple presets in one shot from an activated
[spack environment](https://spack.readthedocs.io/en/latest/environments_basics.html)
(listing multiple specs).
To avoid preset name clashing it's in this case a mandatory to use
spack spec format strings. Some specs can be selected or excluded
(`--exclude`) from your activated environment (for instance for
non-cmake buildable specs).

Advanced usage (preset inheritance)
-----------------------------------

As stated in the cmake documentation:
> CMake supports two main files, CMakePresets.json and
> CMakeUserPresets.json, that allow users to specify common
> configure options and share them with others. CMake also supports
> files included with the include field.

that's why by default `spack preset` create a file named
`CMakeUserPresets.json` from user specific (non shareable)
spack instance.

For separating well known named presets by team developers
with cmake known cached variables from user specific spack
instance (dependencies path, build path...):

1. track with *git* the handwritten `CMakePresets.json` for
the developer team. create well-known named configure and build
presets with well-known cmake cached variables and environment
variable needed. Use the `inherits` directive for using spack created
presets with all dependencies path (`CMAKE_PREFIX_PATH`)
from generated spack formated names. Include it using the
[`include` directive](https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html#includes)
(e.g. `"include": ["CMakeSpackPresets.json"],` for instance).

2. generate (usually from a well-defined spack environment)
base spack presets to be inherited, leveraging the
`-o CMakeSpackPresets.json`, `--hidden` (abstract presets to be inherited
 should be hidden from `cmake --list-presets` command), `--no-build`,
`--no-test` and `--with-name` flags with predefined spack formated names
referenced in `CMakePresets.json`. *git* ignore this generated file.

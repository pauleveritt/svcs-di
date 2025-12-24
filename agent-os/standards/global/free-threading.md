# Python Free Threading Standards

Python 3.14 has optional free threading builds.

## Usage

- The `.python-version` file should end in `t` e.g. `3.14.2t`
- You can confirm the build is free threaded with this:
    ```python
    import sysconfig
    
    is_free_threaded_build = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
    ```
- See [Python Free Threading Guide](https://py-free-threading.github.io) for how to convert a Python project to free
  threaded concurrent safety

## Testing

- The guide has a [page about testing for concurrency safety](https://py-free-threading.github.io/testing/)
- Let's use [pytest-run-parallel](https://github.com/Quansight-Labs/pytest-run-parallel)
- Add a Justfile recipe to run tests in parallel
- Do this in production as well


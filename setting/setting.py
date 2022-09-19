from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=['setting/settings.toml', 'setting/.secrets.toml'],
)

# HERE ENDS DYNACONF EXTENSION LOAD (No more code below this line)
# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.

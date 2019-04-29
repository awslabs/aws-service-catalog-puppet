Utils
=====

The following utils will help you manage your AWS Accounts when using ServiceCatalog-Puppet:


## list-launches
The list-launches command can currently only be invoked on an expanded manifest.yaml file.  To 
expand your manifest you must run the following:

```bash
servicecatalog-puppet expand manifest.yaml
```

This will create a file named ```manifest-expanded.yaml in the same directory```.

You can then run ```list-launches```:
```bash
servicecatalog-puppet list-launches manifest-expanded.yaml
```
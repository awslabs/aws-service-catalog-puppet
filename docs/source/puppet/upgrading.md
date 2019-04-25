Upgrading
=========

Firstly, verify which version you have installed already:

```bash
servicecatalog-puppet version
```

If this errors, check you have activated your virtualenv.

Then you are ready to install the version you want:

```bash
pip install aws-service-catalog-puppet==<version>
```

If you want to upgrade to the latest you can run:

```bash
pip install --upgrade aws-service-catalog-puppet
```

Once you have completed the upgrade you will have to bootstrap your install again:

```bash
servicecatalog-puppet bootstrap
```

And finally, you can verify the upgrade has worked by running version again:

```bash
servicecatalog-puppet version
```
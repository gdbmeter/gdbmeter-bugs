This project aims to provide a basis to study the (logics) bugs found by
[GDBMeter](https://github.com/InverseIntegral/gdbmeter). The format and helper script are based on
[sqlancer/bugs](https://github.com/sqlancer/bugs).

The main file, `bugs.json`, describes the found bugs with additional metadata. You can automatically derive a SQLite
database from the JSON file using the following command:

```shell
./bugs.py export_database
```

In each PR, we automatically validate the JSON file. When changing the file or adding entries to it, be sure to locally
check the file before committing it:

```shell
./bugs.py check
```

To format the JSON file as expected by the check command, you can use the following command:

```shell
./bugs.py format
```

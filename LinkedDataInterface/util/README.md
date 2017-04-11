Util folder
===========


This folder contains some additional utilities that can help in some ways with the LinkedData interface.


## Shiro tools hasher

This tool creates hashed passwords for each user that it is indented to insert into _shiro.ini_ file. The primary idea 
is to avoid the use of plain passwords that might create a security hole in the system.

To use this tool it is only necessary run in a terminal the following command:

```
java -jar shiro-tools-hasher-X.X.X-cli.jar -p
```

When te command is executed, a prompt will ask you to enter a new password

```
Password to hash:
Password to hash (confirm):
```

Once password is entered, the program will return a hashed password with the following format:

```
$shiro1$SHA-256$500000$eWpVX2tGX7WCP2J+jMCNqw==$it/NRclMOHrfOvhAEFZ0mxIZRdbcfqIBdwdwdDXW2dM=
```

This password can be set in the **[Users]** section of the INI file:

```
[users]
...
user1 = $shiro1$SHA-256$500000$eWpVX2tGX7WCP2J+jMCNqw==$it/NRclMOHrfOvhAEFZ0mxIZRdbcfqIBdwdwdDXW2dM=
```

The INI file has the needed configuration to use this feature in the actual version. Only use this tool to create
 new passwords for each user that is indented to access to some parts of the Fuseki's interface.
 
Additional information can be found [here](https://shiro.apache.org/command-line-hasher.html#CommandLineHasher-%7B%7Bshiro.ini%7D%7DUserPasswords)

 
### Credits

This tool is developed by [Apache Shiro](https://shiro.apache.org/)
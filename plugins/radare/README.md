Pre-requisites
--------------

radare2

Setup
-----

r2pm init

r2pm -i lang-python

pip3 install --user r2pipe

Usage
-----

Edit the r2isadetect.py file and check that api_url is correct, localhost
if running your own server in localhost or https://isadetect.com if you
want to use the public one.

Run "r2 -i path/to/r2isadetect.py file_you_want_to_analyze".
For example "r2 -i r2isadetect.py samples/9fb6c8790ddf3632a81fbe0ca96dd3a8.code"

Example
-----

If you run "r2 -i r2isadetect.py samples/9fb6c8790ddf3632a81fbe0ca96dd3a8.code",
and then "aaa", in some versions of r2 you will see an error:

"[Invalid instruction of 1048572 bytes at 0x4 entry0 (aa)".

If you switch to visual mode by inputting "v" and hitting Enter, and then
pressing "p" once to get to see the disassembly, you will see lots of invalid
instructions.

![Invalid instructions](https://i.imgur.com/udA1oYe.png)

If you now exit the visual mode with "q", and type "isadetect", it will send the
file to the API for identification, and print the results in the console.
You can also 'full', 'code' or 'fragment' after "isadetect" command to choose which type of file you are trying to identify,
to possibly get better results.

![Run isadetect](https://i.imgur.com/7lPLqL8.png)

If you go back to the visual mode, you should see no invalid instructions anymore.

![No invalid instructions](https://i.imgur.com/JwxaQ5b.png)

How does it work?
-----

The plugin sends the file to the API, which returns the predicted architecture, endianness and wordsize for the file.

These values are used to set the corresponding values of radare2, so it will analyze the file correctly.

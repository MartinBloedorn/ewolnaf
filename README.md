# ewolnaf
The Eclipse Workaround for Linked Resources that Nobody Asked For

## What does it do?

When working on a project in the Eclipse IDE, you can manually [link files](http://help.eclipse.org/kepler/index.jsp?topic=%2Forg.eclipse.platform.doc.user%2Ftasks%2Ftasks-45.htm) from outside the Workspace. 
The problem, however, is that it is a per-project procedure, that can get tedious very quickly **if you need to add in a lot of external source files.**

The point with `ewolnaf` is to be able do quickly pull in a list of external resources (source files, headers, ASM files, etc.) from Makefile-like list into your workspace. Just close your Eclipse project, run `ewolnaf` and open it again to see the resources.

![Yeah. Good luck adding this per hand.](http://martinvb.com/wp/wp-content/uploads/2017/01/newewolnaf.jpg)

## I didn't ask for this. 

Of course you didn't. It's fairly useless. However, if you're like me and use Eclipse for embedded-software development, you'll find yourself very often having to **link lots of individual source files that are scattered through multiple folders** of, say, a vendor SDK (as happened when working with the [nRF52 SDK](https://www.nordicsemi.com/eng/Products/Bluetooth-low-energy/nRF52832/Development-tools-and-Software)). 

In many cases, you can't simply add the whole source tree, and picking each of the dozens of source files by hand is a PITA. 

However, vendors tend to provide example Makefiles that contain the majority of the resources you need neatly listed out. So I slapped `ewolnaf` together to try to take some advantage of it.

## Still useless, but how do I use it? 

Create a `src.list` file, or modify the included one (the file name doesn't really matter). For example:

    # Libraries and components locations (example)
    SDK_ROOT := /usr/local/lib/nrf52_SDK
    COMP_DIR := $(SDK_ROOT)/components
    
    # Files that will appear in the 'app' virtual folder:
    app/:
    $(COMP_DIR)/libraries/button/app_button.c 
    $(COMP_DIR)/libraries/util/app_error.c
    
    # File that will be on the project root:
    /:
    $(SDK_ROOT)/sdk_config.h
    
Syntax is Makefile-compatible, so you cant copy+paste stuff from existing Makefiles. Once you have your list, close the project in the Eclipse IDE, then push the modifications to the project:

    $ ./ewolnaf.py /path/to/project /path/of/src.list --push
  
You will be prompted to confirm the operation, and a `.project.backup` file will be created. Open the project again, and you're golden (refreshing the file system with F5 may be necessary). 

If you wish to edit existing linked resources, you can first create a `src.list` file from the resources already linked to your project:

    $ ./ewolnaf.py /path/to/project /path/of/src.list --pull
    

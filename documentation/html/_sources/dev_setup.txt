.. _dev_setup:

Setting up for Development
==========================

Install the :ref:`required-software`. 

Sphinxdoc
---------

Sphinxdoc is used to generate documentation from Python docstrings.

It requires `Graphviz <http://www.graphviz.org/>`_ and the python package to be installed to work.

.. code-block::

	conda install graphviz

Graphviz is used to generate diagrams.

Changes to sphinxdoc configuration can be made in conf.py in the `sphinxdoc\\source` directory

In conf.py, change "graphviz_dot" variable so that it points to dot.exe

e.g:

.. code-block:: python

	graphviz_dot='C:/PROGRA~2/Graphviz2.38/bin/dot.exe'

Run `make_html.bat` in the `sphinxdoc` directory to generate HTML documentation.

HTML files should appear in "documentation/html"

Setting up rpy2
---------------

#. *Install necessary Python packages*

	If you haven't done so already. See :ref:`required-software`.

	.. code-block:: bash

		conda install matplotlib pywin32 pandas numpy scipy simplejson

	Download the wheel file for rpy2 from `here <http://www.lfd.uci.edu/~gohlke/pythonlibs/#rpy2>`_

	For 64-bit machines
	rpy2-2.7.2-cp27-none-win_amd64.whl

	For 32-bit machines
	rpy2-2.7.2-cp27-none-win32.whl
	
#. *Install necessary R packages/libraries*

	.. code-block:: R
	
		install.packages("zoo nnls hydromad reshape ggplot2")

#. *Install rpy2*

	From the command line, go to the same folder as the '.whl' file \
	Then run the following command

	.. code-block:: bash

		pip install rpy2-2.7.2-cp27-none-win_amd64.whl

	Replace the above filename with the correct one if necessary

#. Set system or user environment variables

	* R_HOME
	
	  Should be set to the R folder
	  
	  e.g. `C:\\Program Files\\R\\R-3.1.2`

	* R_USER
	  Should point to the location of the parent folder of where R libraries are installed
	  
	  On Windows machines, they should be in a folder called "win-library"
	  
	  Usually this is in the user profile folder 
	
	e.g. if the win-libary folder is located at
	`C:\\users\\\[username\]\\Documents\\R\\win-libary`
	
	Then R_USER should point to
	`C:\\users\\\[username\]\\Documents`
	
	If the model crashes with error message

		:code:`Import Error (ie)`

	or similar (something related to 'ie'), then there is a problem with how you set the above environment variables.



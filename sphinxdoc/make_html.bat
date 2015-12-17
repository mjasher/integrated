@echo off
echo WARNING: THIS WILL DELETE/OVERWRITE EXISTING FILES
echo PRESS CTRL+C TO CANCEL IF THIS IS NOT DESIRED
pause

echo Clearing pre-existing files...
echo "-----------------------------"
del %cd%\apidoc\*.rst /Q

echo Generating documentation files...
echo "-----------------------------"
sphinx-apidoc -o %cd%\apidoc ..\ -s rst

echo Copying files to source directory
echo "-----------------------------"
xcopy /s /Y %cd%\apidoc %cd%\source

echo Generating HTML documentation
echo "-----------------------------"
make html
# GÉANT Python assessment questions

## Discussion

1. Describe how to release a python application.
2. Describe how to test python applications, and integrate testing into the release process.
3. What are some uses of the `yield` keyword?
4. What is the result of the following expression?
   ```python
    reduce(lambda x,y: x+y, range(5))
    ```

## Written exercises

5. Do a code review of the file
   `sql_cli.py` in this repository.

6. Package `sql_cli.py` to be releasable as a python package.
   * It should be installable using `pip` and when installed the
     script `sql_cli.py` should be executable from the command line
     by running the command `check-sql` (with appropriate arguments).
   * Packaging should be convenient for release of consecutive
     versions via a package repository such as pypi.org.
   * Add a trivial unit test and show how to automate execution
     of all unit tests with Jenkins, Travis CI, or 
     some other CI framework.
   * Explain how to integrate testing against multiple Python
     interpreter versions with the CI framework you chose.
   * Propose a branching model for managing changes and releases.

7. Write a method that accepts an iterable of integers
   as input and returns an iterable containing all prime
   integers.
   * Add a parameter that specifies the number of threads
     that should be used to perform computations in parallel.

8. Describe the suitability of the file
   `site.cert` in this repository for use
   with a web server.


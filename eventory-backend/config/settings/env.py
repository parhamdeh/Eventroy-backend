"""
Load environment variables for Django project.

This module is written to load defined environment variables. To read the variables, we use the django_environ
package.
"""

from environ import Env

env = Env()
env.read_env(env_file=".env")

Installation
============

Requirements
------------

Python 3.13 or later and `uv <https://docs.astral.sh/uv/>`_ are required.

Install the project
-------------------

Clone the repository and, from its root directory, install the project and
its dependencies:

.. code-block:: console

   uv sync

To install the development dependencies as well (including Sphinx and pytest),
run:

.. code-block:: console

   uv sync --group dev

You can then run the test suite with:

.. code-block:: console

   uv run pytest

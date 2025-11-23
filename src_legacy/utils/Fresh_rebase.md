# Fresh software rebase

## Technical details

Datamanip is a numerical data processing and visualization application built using the PySide6 framework. It is designed to facilitate data manipulation tasks commonly encountered in experimental sciences. The application leverages the Model-View-Controller (MVC) design pattern to ensure a clear separation of concerns, enhancing maintainability and scalability.

The core functionalities of Datamanip include:
- Data Import and Export: Supports various data formats commonly used in scientific research.
- Data Manipulation: Provides tools for filtering, transforming, and analyzing datasets.
- Visualization: Offers a range of plotting options to visualize data effectively.
- User Interface: Built with PySide6 to provide a responsive and user-friendly experience.
The application is structured to allow easy integration of new features and improvements, adhering to best practices in software development.

## Rebase process

The software will be able to open Workspaces of deifferent kind :

- Numerical Analysis Workspaces
- Image Analysis Workspaces (in the future)
- Others (in the future)

A workspace is a tabbed interface that contains multiple "studies". Each workspace type will have its own set of functionalities and tools tailored to the specific data analysis needs.
Each study contains data objects, visualizations, and analysis results relevant to a particular experiment or dataset, which results are available across all workspaces.

For example a workspace could have a Numercial Data Table study, a Visualization study, a Statistics study, a Fitting study, etc.

The rebase process involves the following steps:

Use a single DataObject structure across all workspaces to represent and manage data consistently. Lets say a pandas DataFrame for numerical data.

1. Numerical Analysis Workspace:
   - Implement data manipulation tools specific to numerical datasets.
   - A DataTable containing DataObjects :
        - Implement sorting, filtering, and transformation functionalities.
        - Ensure efficient handling of large datasets.
        - Multiple DataObjects type such has, formulas calculated from other constants and tables. Interpolation table, range tables, etc.
   - Integrate visualization options for numerical data (e.g., line plots, scatter plots).
   - Ensure compatibility with existing numerical data formats.

# Architecture Overview

All data should have a unified representation using DataObjects. Each DataObject can represent different types of data, such as numerical tables, images, or other formats.
Formula engine should be unified for scalars, arrays and tables, and be unit aware and propagate uncertainties when those tables type are implemented.


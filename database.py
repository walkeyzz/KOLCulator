from sqlalchemy import create_engine, MetaData
from sqlalchemy_schemadisplay import create_schema_graph

# Replace 'sqlite:///your_database.db' with your actual database URL
engine = create_engine('sqlite:///users.db')

# Generate the ERD
graph = create_schema_graph(metadata=MetaData(bind=engine),
                            show_datatypes=True, # Show data types of columns
                            show_indexes=True, # Show indexes
                            rankdir='LR', # Left to right layout
                            concentrate=False) # Avoid merging edges

# Save the ERD to a file
graph.write_png('ERD.png') # You can also save as .dot or .pdf

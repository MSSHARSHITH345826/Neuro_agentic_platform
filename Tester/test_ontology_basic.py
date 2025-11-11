import sys
import os

# Ensure the parent directory is in the Python path so 'ontology' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ontology import OntologyManager

def test_ontology_loading():
    file_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'Data',
        'Ontology_test_data',
        '1_sample_individual.owl'
    )
    manager = OntologyManager(file_path)
    print("Ontology loaded successfully.")

    # Test: Classes
    classes = manager.get_classes()
    print("Classes found:", [str(c).split('#')[-1] for c in classes])

    # Test: Individuals of class 'Patient'
    patients = manager.get_individuals('Patient')
    print("Patients:", [str(p).split('#')[-1] for p in patients])

    # Test: Object properties
    obj_props = manager.get_object_properties()
    print("Object Properties:", [str(p).split('#')[-1] for p in obj_props])

    # Test: Properties of Patient1
    patient1 = manager.get_individual_by_name('Patient1')
    if patient1:
        props = manager.get_individual_properties(patient1)
        print("Properties for Patient1:")
        for pred, obj in props:
            pred_name = str(pred).split('#')[-1] if '#' in str(pred) else str(pred)
            obj_name = str(obj).split('#')[-1] if '#' in str(obj) else str(obj)
            print(f"  {pred_name} -> {obj_name}")
    else:
        print("Patient1 not found.")

if __name__ == "__main__":
    test_ontology_loading()

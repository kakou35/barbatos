"""
Tests pour la boucle de raisonnement ReAct et l'extraction JSON (ai.brain).
"""

from ai.brain import brain


def test_extract_json_block_markdown():
    text = """
    Voici mon raisonnement :
    ```json
    {
      "thought": "Vérifier le processeur",
      "action": "get_hardware_status",
      "action_input": {}
    }
    ```
    """
    block = brain._extract_json_block(text)
    assert block is not None
    assert block["action"] == "get_hardware_status"


def test_extract_json_block_raw():
    text = '{"thought": "Fin de mission", "final_answer": "Bonjour le monde"}'
    block = brain._extract_json_block(text)
    assert block is not None
    assert block["final_answer"] == "Bonjour le monde"


if __name__ == "__main__":
    test_extract_json_block_markdown()
    test_extract_json_block_raw()
    print("Tests Brain validés avec succès !")

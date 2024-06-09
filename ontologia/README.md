**Ontologias presentes**

- *supernatural.ttl* -> criada no Protege, é a ontologia que iremos popular

- *output2.ttl* -> ontologia já populada e que irá para o sparql e irá fornecer os dados para a api 

**Instruções para popular ontologia**

1. Executar Web Scrapping na página wiki mencionada no relatório, correndo o programa supernatural.py.
2. Após isto, obtemos um supernatural.json, ao qual depois retiramos todas as entradas "Category:".
3. Otemos o origin.json, recorrendo ao chatGPT e a indo buscar informação à mão.
4. Calculos dos ratings já estão no populate.py, mas foram também obtidos à mão.
5. Executar populate.py, o que resulta na output2.ttl.

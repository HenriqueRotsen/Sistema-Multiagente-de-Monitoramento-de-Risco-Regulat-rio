"""Testes unitários para TextProcessor."""
import unittest

from src.utils.data_collection import TextProcessor


class TestExtractSections(unittest.TestCase):
    def test_cabecalho_e_artigos(self):
        text = (
            "BANCO CENTRAL DO BRASIL\nResolução BCB nº 1\n\n"
            "CONSIDERANDO a necessidade de regulamentar;\n\n"
            "Art. 1 As instituições financeiras devem cumprir.\n"
            "Art. 2 O prazo é de 90 dias.\n\n"
            "VIGÊNCIA Esta resolução entra em vigor na data de publicação."
        )
        sections = TextProcessor.extract_sections(text)
        self.assertIn("cabecalho", sections)
        self.assertIn("considerandos", sections)
        self.assertIn("vigencia", sections)
        self.assertTrue(len(sections["cabecalho"]) > 0)

    def test_texto_vazio(self):
        self.assertEqual(TextProcessor.extract_sections(""), {})

    def test_numera_artigos(self):
        text = (
            "Art. 1 Primeira obrigação.\n"
            "Art. 2 Segunda obrigação.\n"
        )
        sections = TextProcessor.extract_sections(text)
        self.assertIn("artigos", sections)


class TestExtractDates(unittest.TestCase):
    def test_formato_dd_mm_yyyy(self):
        result = TextProcessor.extract_dates("Vigência a partir de 30/01/2025.")
        self.assertTrue(any(r["date"] == "2025-01-30" for r in result))

    def test_formato_iso(self):
        result = TextProcessor.extract_dates("Data limite: 2025-12-31.")
        self.assertTrue(any(r["date"] == "2025-12-31" for r in result))

    def test_formato_extenso(self):
        result = TextProcessor.extract_dates("Aprovada em 15 de março de 2024.")
        self.assertTrue(any(r["date"] == "2024-03-15" for r in result))

    def test_referencia_relativa(self):
        result = TextProcessor.extract_dates("Vigência imediata a partir da publicação.")
        self.assertTrue(any(r["type"] == "relative" for r in result))

    def test_texto_sem_datas(self):
        result = TextProcessor.extract_dates("Texto sem data nenhuma.")
        self.assertEqual(result, [])

    def test_texto_vazio(self):
        self.assertEqual(TextProcessor.extract_dates(""), [])

    def test_sem_duplicatas(self):
        result = TextProcessor.extract_dates("Data 01/01/2025 e data 01/01/2025 novamente.")
        dates = [r["text"] for r in result]
        self.assertEqual(len(dates), len(set(dates)))


class TestExtractObligations(unittest.TestCase):
    def test_verbo_devera(self):
        text = "As instituições financeiras deverão manter registros por 5 anos."
        result = TextProcessor.extract_obligations(text)
        self.assertTrue(len(result) > 0)
        self.assertTrue(any("deverão" in r for r in result))

    def test_verbo_devem(self):
        text = "Os bancos devem reportar operações suspeitas ao BACEN."
        result = TextProcessor.extract_obligations(text)
        self.assertTrue(len(result) > 0)

    def test_fica_vedado(self):
        text = "Ficam vedadas operações acima do limite estabelecido."
        result = TextProcessor.extract_obligations(text)
        self.assertTrue(len(result) > 0)

    def test_sem_obrigacoes(self):
        text = "Este documento informa sobre as condições do mercado."
        result = TextProcessor.extract_obligations(text)
        self.assertEqual(result, [])

    def test_texto_vazio(self):
        self.assertEqual(TextProcessor.extract_obligations(""), [])

    def test_sem_duplicatas(self):
        text = "As IFs deverão reportar. As IFs deverão reportar."
        result = TextProcessor.extract_obligations(text)
        self.assertEqual(len(result), 1)


class TestExtractEntities(unittest.TestCase):
    def test_banco_central(self):
        text = "O Banco Central determinou novas regras para PIX."
        result = TextProcessor.extract_entities(text)
        self.assertIn("Banco Central", result)
        self.assertIn("PIX", result)

    def test_cvm_e_fintechs(self):
        text = "A CVM publicou instrução aplicável a fintechs e bancos."
        result = TextProcessor.extract_entities(text)
        self.assertIn("CVM", result)
        self.assertIn("fintechs", result)
        self.assertIn("bancos", result)

    def test_sem_entidades(self):
        text = "O céu está azul hoje."
        result = TextProcessor.extract_entities(text)
        self.assertEqual(result, [])

    def test_texto_vazio(self):
        self.assertEqual(TextProcessor.extract_entities(""), [])

    def test_sem_duplicatas(self):
        text = "O Banco Central e o Banco Central novamente."
        result = TextProcessor.extract_entities(text)
        self.assertEqual(result.count("Banco Central"), 1)


if __name__ == "__main__":
    unittest.main()

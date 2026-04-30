import unittest
import sys
import os

# Ajustar PYTHONPATH para permitir la importación desde src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from protocol.serializer import (
    deserialize_message, serialize_response, serialize_request,
    BusMessage, DESER_OK, DESER_ERROR, MAX_MSG_LEN, MAX_DATA_LEN
)

class TestDeserializeMessage(unittest.TestCase):
    def test_deserialize_valid_with_data(self):
        """[Clase Válida] Mensaje completo que requiere dato entero."""
        raw = "LIST|INSERT|0|42\n"
        code, msg = deserialize_message(raw)
        self.assertEqual(code, DESER_OK)
        self.assertEqual(msg.obj_type, "LIST")
        self.assertEqual(msg.operation, "INSERT")
        self.assertEqual(msg.instance_id, 0)
        self.assertEqual(msg.data_int, 42)

    def test_deserialize_valid_without_data(self):
        """[Clase Válida] Mensaje que no requiere dato extra."""
        raw = "STACK|POP|1|\n"
        code, msg = deserialize_message(raw)
        self.assertEqual(code, DESER_OK)
        self.assertEqual(msg.operation, "POP")
        self.assertFalse(msg.has_data)

    def test_deserialize_none_or_empty(self):
        """[Clase Inválida] Pasar None o string vacío."""
        code, msg = deserialize_message(None)
        self.assertEqual(code, DESER_ERROR)
        code2, msg2 = deserialize_message("")
        self.assertEqual(code2, DESER_ERROR)

    def test_deserialize_missing_terminator(self):
        """[Caso Especial] String sin el salto de línea obligatorio."""
        raw = "TREE|CREATE|0|"
        code, msg = deserialize_message(raw)
        self.assertEqual(code, DESER_ERROR)

    def test_deserialize_invalid_separators(self):
        """[Clase Inválida] Faltan separadores |."""
        raw = "LISTCREATE042\n"
        code, msg = deserialize_message(raw)
        self.assertEqual(code, DESER_ERROR)

    def test_deserialize_invalid_data_type(self):
        """[Clase Inválida] Operación que exige int recibe un string."""
        raw = "LIST|INSERT|0|letras\n"
        code, msg = deserialize_message(raw)
        self.assertEqual(code, DESER_ERROR)

    def test_deserialize_max_length(self):
        """[Límite Superior] Mensaje excediendo tamaño máximo (MAX_MSG_LEN)."""
        huge_data = "A" * 1500
        raw = f"LIST|INSERT|0|{huge_data}\n"
        code, msg = deserialize_message(raw)
        self.assertEqual(code, DESER_ERROR)

class TestSerializeResponse(unittest.TestCase):
    def test_serialize_response_success(self):
        """[Clase Válida] Éxito con datos numéricos."""
        res = serialize_response(True, "42")
        self.assertEqual(res, "OK|42\n")

    def test_serialize_response_error(self):
        """[Clase Válida] Error con código de texto."""
        res = serialize_response(False, "INSTANCE_NOT_FOUND")
        self.assertEqual(res, "ERROR|INSTANCE_NOT_FOUND\n")

    def test_serialize_response_empty_data(self):
        """[Límite Inferior] Dato vacío."""
        res = serialize_response(True, "")
        self.assertEqual(res, "OK|\n")

    def test_serialize_response_truncation(self):
        """[Límite Superior] Truncamiento de dato muy largo."""
        huge_data = "X" * 300
        res = serialize_response(True, huge_data)
        self.assertTrue(res.endswith("\n"))
        self.assertTrue(res.startswith("OK|"))
        # El tamaño del dato truncado debe ser exactamente MAX_DATA_LEN
        self.assertEqual(len(res.split("|")[1].strip()), MAX_DATA_LEN)

    def test_serialize_response_special_chars(self):
        """[Caso Especial] Retorno con caracteres especiales."""
        res = serialize_response(False, "C@S0_%!")
        self.assertEqual(res, "ERROR|C@S0_%!\n")

class TestSerializeRequest(unittest.TestCase):
    def test_serialize_request_with_data(self):
        """[Clase Válida] Petición completa con datos."""
        req = serialize_request("TREE", "INSERT", 5, "99")
        self.assertEqual(req, "TREE|INSERT|5|99\n")

    def test_serialize_request_without_data(self):
        """[Clase Válida] Petición sin dato final explícito."""
        req = serialize_request("LIST", "SIZE", 1, "")
        self.assertEqual(req, "LIST|SIZE|1|\n")

    def test_serialize_request_default_data(self):
        """[Límite Inferior] Uso del argumento por defecto."""
        req = serialize_request("STACK", "POP", 2)
        self.assertEqual(req, "STACK|POP|2|\n")

    def test_serialize_request_id_zero(self):
        """[Límite Inferior] Instance ID en 0."""
        req = serialize_request("TREE", "CREATE", 0)
        self.assertEqual(req, "TREE|CREATE|0|\n")

    def test_serialize_request_negative_data(self):
        """[Caso Especial] Dato numérico negativo."""
        req = serialize_request("LIST", "INSERT", 1, "-500")
        self.assertEqual(req, "LIST|INSERT|1|-500\n")

if __name__ == '__main__':
    unittest.main()

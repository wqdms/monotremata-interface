import os
import mimetypes
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
import pandas as pd
from pprint import pp
from monotremata.models import PresetModelField, Document
from monotremata.presets import validate_name, validate_is_not_numeric_value
from django.core.exceptions import ValidationError, ImproperlyConfigured
from rest_framework.exceptions import APIException
from monotremata.middleware import error_message
DJANGO_PORT = os.getenv("DJANGO_PORT", "8000")
import io

def combine_execl_dataframes(dfx,dfy,sheetx,sheety):
    # 1. Create a buffer
    output = io.BytesIO()

    # 2. Use the buffer as the file path for ExcelWriter
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        dfx.to_excel(writer, sheet_name=sheetx)
        dfy.to_excel(writer, sheet_name=sheety)

    # 3. Seek to the beginning of the buffer so it can be read
    output.seek(0)
    return output

file_format_mapping = {
    "xlsx": "excel",
    "xls": "execl",
    "xlsm": "execl",
    "xlsb": "execl",
}


def to_preset_model_field_schema(
    fieldName,
    fieldDataType,
    label,
    fieldParameters="",
    sorting=0.0,
    instance: Document = None,
):
    result = {
        "fieldDataType": f"Preset.map_{fieldDataType}",
        "fieldName": fieldName.strip().rstrip(),
        "fieldParameters": fieldParameters,
        "label": label,
        "sorting": sorting,
        "valid_name": True,
    }
    if instance:
        result["tag"] = instance.tag
        if not label:
            result["label"] = instance.label
    try:
        validate_name(result["fieldName"])
        validate_is_not_numeric_value(result["fieldName"])

    except ValidationError as e:
        result["error_message"] = {
            "field_name_error": {"initial": str(e)},
            "originalFieldName": result["fieldName"],
        }
        result["valid_name"] = False

    return result


class DocumentParser:
    def __init__(self, instance: Document):
        self.instance = instance
        self.sheet_name = instance.sheet_name
        self.sheet_names = instance.sheet_names
        self.label = instance.label
        self.file = instance.file_upload.file

    def csv(self, get_array: bool = False):
        if self.sheet_name is None:
            if self.label:
                self.sheet_name = self.label.split("/")[-1].split(".")[0]
            else:
                self.sheet_name = f"sheet-{self.instance.name}-{self.instance.id}"
        df = pd.read_csv(self.file)
        if get_array:
            return [{"sheet": self.sheet_name, "columns": df.columns}]
        return df

    def xlsx(self,sheet_name:str=None, get_array: bool = False):
        df = None
        try:
            df = pd.read_excel(self.file, sheet_name=sheet_name)
        except Exception as e:
            print(f"DocumentParser warning: {e}")

        if get_array:
            return [
                {
                    "sheet": self.sheet_name
                    or f"sheet-{self.instance.name}-{self.instance.id}",
                    "columns": df.columns,
                }
            ]
        return df

    def json(self, get_array: bool = False):
        df: dict[str, pd.DataFrame] = pd.read_json(
            self.file, sheet_name=self.sheet_name
        )
        if get_array:
            return [
                {
                    "sheet": self.sheet_name
                    or f"sheet-{self.instance.name}-{self.instance.id}",
                    "columns": df.columns,
                }
            ]
        return df

    def __call__(self, *args, **kwargs):
        has = None
        try:
            has = getattr(self, self.instance.file_format, None)
        except Exception as e:
            print(f"DocumentParser warning: {e}")
        if has:
            return has(*args, **kwargs)
        return None


class Command(BaseCommand):
    help = "write / add a value to a list in a script file"

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--file_paths",
            required=False,
            default="",
            type=str,
            help="""comma seperated string of file_paths, save dataset entity attribute to PresetModelField""",
        )
        parser.add_argument(
            "-ids",
            "--document_ids",
            default="",
            required=False,
            type=str,
            help="""comma seperated list of document ids, saves dataset entity attribute to PresetModelField""",
        )

    def handle(self, *args, **options):
        file_paths = options.get("file_paths", str("")).split(",")
        document_ids = options.get("document_ids", str("")).split(",")

        data = list()
        try:
            if file_paths:
                for i in file_paths:
                    if os.path.exists(i):
                        print(mimetypes.guess_type(i))
                        _file_format = i.split(".")[-1]
                        file_format = file_format_mapping.get(
                            _file_format, _file_format
                        )
                        x = getattr(pd, f"read_{file_format}")(i)
                        data += [
                            to_preset_model_field_schema(
                                column[0], column[1].name, i.label, ""
                            )
                            for column in x.dtypes.items()
                        ]
            if document_ids:
                for i in Document.objects.filter(id__in=document_ids):
                    # file_format = file_format_mapping.get(i.file_format, i.file_format)
                    # x = getattr(pd, f"read_{file_format}")(i.file_upload)
                    X = DocumentParser(instance=i)
                    sheets = []
                    if i.sheet_names:
                        sheets = [s for s in i.sheet_names if s not in  [i.sheet_name]]
                    if i.sheet_name:
                        sheets.append(i.sheet_name)
                    
                    file_format = file_format_mapping.get(i.file_format, i.file_format)
                    if file_format in ["excel"] and not sheets and i.file_upload:
                        sheets = [None]
                        
                    for sheet in sheets:
                        x = X(sheet_name=sheet)
                        data += [
                            to_preset_model_field_schema(
                                column[0], column[1].name, sheet, "", instance=i
                            )
                            for column in x.dtypes.items()
                        ]

            if data:
                # pp(data)
                for i in data:
                    n, c = PresetModelField.objects.update_or_create(**i)
                    print([i["fieldName"], n, c])
                return self.stdout.write("ok")
        except AttributeError as e:
            msg = f"Add sheet_names or sheet_name to Document | error: {e}"
            self.stdout.write(msg)
            error_message(msg)
            #raise APIException(msg)
        except Exception as e:
            self.stdout.write(f"error: {e}")
        else:
            call_command("parser", "-h")

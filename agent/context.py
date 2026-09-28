from core.models import Result

def read_source(path):

    target = {"file": path,
              "source": ''}

    with open(path, 'r') as file:
        target['source'] = file.read()

    return target

def build_context(Result:Result):
    CONTEXT = {}

    CONTEXT['target'] = read_source(Result.file)
    CONTEXT['findings'] = Result.plg_data
    CONTEXT['errors'] = Result.errors

    return CONTEXT
    
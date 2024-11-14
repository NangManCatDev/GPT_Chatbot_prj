1. query에 대한 response를 낼 때, 이전 query에 대한 response까지 같이 출력하는 문제가 발생

2. temperature, top_p, top_k가 적용되지 않는 문제

3. query를 던졌을 떄, 아래와 같은 문제가 발생.
```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "C:\vscode_prj\Gemini-Waifu\test.py", line 60, in <module>
    response = model.generate_content(prompt)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\1\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\generativeai\generative_models.py", line 331, in generate_content
    response = self._client.generate_content(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\1\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\ai\generativelanguage_v1beta\services\generative_service\client.py", line 827, in generate_content
    response = rpc(
               ^^^^
  File "C:\Users\1\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\gapic_v1\method.py", line 131, in __call__
    return wrapped_func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    return retry_target(
           ^^^^^^^^^^^^^
  File "C:\Users\1\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_unary.py", line 153, in retry_target
    _retry_error_helper(
  File "C:\Users\1\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_base.py", line 212, in _retry_error_helper
    raise final_exc from source_exc
  File "C:\Users\1\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\retry\retry_unary.py", line 144, in retry_target
    result = target()
             ^^^^^^^^
  File "C:\Users\1\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\timeout.py", line 120, in func_with_timeout
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\1\AppData\Local\Programs\Python\Python312\Lib\site-packages\google\api_core\grpc_helpers.py", line 78, in error_remapped_callable
    raise exceptions.from_grpc_error(exc) from exc
google.api_core.exceptions.InternalServerError: 500 An internal error has occurred. Please retry or report in https://developers.generativeai.google/guide/troubleshooting
```
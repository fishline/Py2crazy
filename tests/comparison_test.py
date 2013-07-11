x = foo + bar < bazzz

'''
pgbovine@pg-mba ~/Py2crazy
$ Python-2.7.5/python.exe -m dis tests/comparison_test.py 
  1      (1, 4)(4, 3)            0 LOAD_NAME                0 (foo)
       (1, 10)(10, 3)            3 LOAD_NAME                1 (bar)
         (1, 8)(4, 9)            6 BINARY_ADD          
       (1, 16)(16, 5)            7 LOAD_NAME                2 (bazzz)
       (1, 14)(4, 17)           10 COMPARE_OP               0 (<)
         (1, 0)(0, 1)           13 STORE_NAME               3 (x)
         (1, 0)(0, 1)           16 LOAD_CONST               0 (None)
         (1, 0)(0, 1)           19 RETURN_VALUE      
'''

all:
	g++ -shared -fPIC -o aeb_lib.so aeb_logic.cpp

coverage:
	g++ -shared -fPIC --coverage -O0 -g -o aeb_lib.so aeb_logic.cpp

valgrind_build:
	g++ -g --coverage -c aeb_logic.cpp
	g++ -g --coverage -c valgrind_test.cpp
	g++ -g --coverage -o valgrind_test valgrind_test.o aeb_logic.o

clean:
	rm -f aeb_lib.so valgrind_test *.gcda *.gcno *.gcov

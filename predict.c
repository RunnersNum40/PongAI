#include <stdio.h>
#include <math.h>

double predict(float old_y, float old_x, float new_x, float new_y, int table_x[2], int table_y[2]) {
	if(new_x-old_x < 0) {
		int tx = table_x[0];
	}
	else if(new_x-old_x > 0) {
		int tx = table_x[1];
	}
	else {
		return new_y;
	}

	float dx = new_x-old_x;
	float dy = new_y-old_y;
	float m = dy/dx;

	float l = m*tx+new_y-m*new_x;
	double p = floor(l/table_y[1]);

	return table_y[1]*p%2+pow((double)-1, p)*(l%table_y[1]);
}

int main( int argc, char *argv[] )  {
   if( argc == 2 ) {
      printf("The argument supplied is %s\n", argv[1]);
   }
   else if( argc > 2 ) {
      printf("Too many arguments supplied.\n");
   }
   else {
      printf("One argument expected.\n");
   }
}
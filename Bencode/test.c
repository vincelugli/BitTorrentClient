#define FILE_IO

#include <stdio.h>
#include <string.h>
#ifdef FILE_IO
#include <sys/stat.h>
#include <stdlib.h>
#endif
#include "bencode.h"

char *read_file(const char *file, long long *len)
{
#ifdef FILE_IO
	struct stat st;
	char *ret = NULL;
	FILE *fp;

	if (stat(file, &st))
		return ret;
	*len = st.st_size;

	fp = fopen(file, "r");
	if (!fp)
		return ret;

	ret = malloc(*len);
	if (!ret)
		return NULL;

	fread(ret, 1, *len, fp);

	fclose(fp);

	return ret;
#else
	return NULL;
#endif
}

int main(int argc, char *argv[])
{
	int i;

	setbuf(stdout, NULL);

	for (i = 1; i < argc; ++i) {
		char *buf;
		long long len;
		be_node *n;

		buf = read_file(argv[i], &len);
		if (!buf) {
			buf = argv[i];
			len = strlen(argv[i]);
		}

		printf("DECODING: %s\n", argv[i]);
		n = be_decoden(buf, len);
		if (n) {
			be_dump(n);
			be_free(n);
		} else
			printf("\tparsing failed!\n");

#ifdef FILE_IO
		if (buf != argv[i])
			free(buf);
#endif
	}

	return 0;
}

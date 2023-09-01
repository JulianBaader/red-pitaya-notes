/*
command to compile:
gcc -O3 test-signal-continuity.c -lm -o test-signal-continuity
*/

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/types.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define TCP_ADDR "192.168.1.100"
#define TCP_PORT 1001

#define N 524288

int main()
{
  int i, sock, size;
  struct sockaddr_in addr;
  int32_t *data, d, dmax;
  uint32_t command[3];

  data = malloc(16 * N);

  if((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0)
  {
    perror("socket");
    return 1;
  }

  memset(&addr, 0, sizeof(addr));
  addr.sin_family = AF_INET;
  addr.sin_addr.s_addr = inet_addr(TCP_ADDR);
  addr.sin_port = htons(TCP_PORT);

  if(connect(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0)
  {
    perror("connect");
    return 1;
  }

  size = 131072;

  for(i = 0; i < size; ++i)
  {
    data[i * 4 + 0] = (int32_t)floor(2.1e9 * cos(2.0 * M_PI * i / size) + 0.5);
    data[i * 4 + 1] = (int32_t)floor(2.1e9 * sin(2.0 * M_PI * i / size) + 0.5);
    data[i * 4 + 2] = 0;
    data[i * 4 + 3] = 0;
  }

  command[0] = 20;
  command[1] = (1 << 28) + 10000000;
  command[2] = (2 << 28) + (16 * size);
  send(sock, command, 12, MSG_NOSIGNAL);
  send(sock, data, 16 * size, MSG_NOSIGNAL);

  command[0] = (3 << 28);
  send(sock, command, 4, MSG_NOSIGNAL);

  while(1)
  {
    recv(sock, data, 16 * N, MSG_WAITALL);
    dmax = 0;
    for(i = 1; i < N; ++i)
    {
      d = abs(data[i * 4] - data[(i - 1) * 4]);
      if(dmax < d) dmax = d;
    }
    if(dmax > 1000000) printf("%d\n", dmax);
  }

  return 0;
}
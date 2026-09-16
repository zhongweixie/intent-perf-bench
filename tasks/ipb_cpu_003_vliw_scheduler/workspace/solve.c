#include "solve.h"
#include <stdlib.h>
#include <string.h>

/* An edge says that 'to' cannot issue until delay cycles after 'from'.
 * RAW edges carry the producer latency; WAW edges need one cycle (writes in
 * one bundle are simultaneous), and WAR edges need no data latency. */
typedef struct Edge {
    int to, delay, next;
} Edge;

typedef struct Reader {
    int op, next;
} Reader;

static int lat(OpType t)
{
    return t == OP_MUL ? 3 : t == OP_MEM ? 4 : 1;
}

static const VliwBundle empty_bundle = {
    { OP_NOP, -1, -1, -1, 0, -1 },
    { OP_NOP, -1, -1, -1, 0, -1 },
    { OP_NOP, -1, -1, -1, 0, -1 }
};

static void edge_add(Edge **ep, int *ne, int *cap, int *head,
                     int from, int to, int delay)
{
    if (*ne == *cap) {
        *cap = *cap ? *cap * 2 : 256;
        *ep = (Edge *)realloc(*ep, (size_t)*cap * sizeof **ep);
    }
    (*ep)[*ne] = (Edge){ to, delay, head[from] };
    head[from] = (*ne)++;
}

int vliw_schedule(const VliwOp *ops, int n_ops, VliwBundle *out)
{
    int *head = (int *)malloc((size_t)n_ops * sizeof *head);
    int *indeg = (int *)calloc((size_t)n_ops, sizeof *indeg);
    int *last = (int *)malloc(VLIW_REGS * sizeof *last);
    int *rhead = (int *)malloc(VLIW_REGS * sizeof *rhead);
    int *rnext = (int *)malloc((size_t)(2 * n_ops) * sizeof *rnext);
    Edge *edges = NULL;
    Reader *readers = (Reader *)malloc((size_t)(2 * n_ops) * sizeof *readers);
    int nr = 0, ne = 0, ecap = 0;

    for (int r = 0; r < VLIW_REGS; ++r) last[r] = rhead[r] = -1;
    for (int i = 0; i < n_ops; ++i) head[i] = -1;

    /* Construct the true program-order dependency graph.  In particular,
     * WAW and WAR edges are required: merely tracking the last RAW writer
     * changes the final register file when instructions are reordered. */
    for (int i = 0; i < n_ops; ++i) {
        int rd = ops[i].rd;
        int reads[2] = { ops[i].rs1, ops[i].rs2 };
        int nrds = (reads[0] >= 0 && reads[0] < VLIW_REGS && reads[0] != 0);
        int nr2  = (reads[1] >= 0 && reads[1] < VLIW_REGS && reads[1] != 0 && reads[1] != reads[0]);

        /* RAW dependencies use the writer which was current in the input
         * program.  r0 is constant and therefore has no dependency. */
        if (nrds && last[reads[0]] >= 0) {
            int p = last[reads[0]];
            edge_add(&edges, &ne, &ecap, head, p, i, lat(ops[p].type));
            ++indeg[i];
        }
        if (nr2 && last[reads[1]] >= 0) {
            int p = last[reads[1]];
            edge_add(&edges, &ne, &ecap, head, p, i, lat(ops[p].type));
            ++indeg[i];
        }

        if (rd > 0 && rd < VLIW_REGS) {
            if (last[rd] >= 0) {
                edge_add(&edges, &ne, &ecap, head, last[rd], i, 1);
                ++indeg[i];
            }
            for (int q = rhead[rd]; q >= 0; q = readers[q].next) {
                edge_add(&edges, &ne, &ecap, head, readers[q].op, i, 0);
                ++indeg[i];
            }
            rhead[rd] = -1;
            last[rd] = i;
        }

        /* This read must also happen before a later overwrite.  Add it only
         * after handling the current write, so read/modify/write is not a
         * self-edge. */
        if (nrds) {
            readers[nr] = (Reader){ i, rhead[reads[0]] };
            rhead[reads[0]] = nr; rnext[nr++] = 0;
        }
        if (nr2) {
            readers[nr] = (Reader){ i, rhead[reads[1]] };
            rhead[reads[1]] = nr; rnext[nr++] = 0;
        }
    }

    /* Longest downstream path is a useful priority on the adversarial input:
     * it keeps MUL chains fed while filling unrelated ALU/MEM slots. */
    int *critical = (int *)calloc((size_t)n_ops, sizeof *critical);
    for (int i = n_ops - 1; i >= 0; --i) {
        for (int e = head[i]; e >= 0; e = edges[e].next) {
            int v = edges[e].to;
            int x = edges[e].delay + critical[v];
            if (x > critical[i]) critical[i] = x;
        }
    }

    unsigned char *done = (unsigned char *)calloc((size_t)n_ops, 1);
    int *release = (int *)calloc((size_t)n_ops, sizeof *release);
    int remaining = n_ops, cycle = 0;
    while (remaining) {
        VliwBundle b = empty_bundle;
        int picked[3] = { -1, -1, -1 };
        int used_type[4] = { 0, 0, 0, 0 };

        /* Pick one best ready operation for each of the three distinct slots. */
        for (int pass = 0; pass < 3; ++pass) {
            int best = -1;
            for (int i = 0; i < n_ops; ++i) {
                int t = ops[i].type;
                if (done[i] || indeg[i] || release[i] > cycle || t < OP_ALU || t > OP_MEM || used_type[t]) continue;
                if (best < 0 || critical[i] > critical[best] ||
                    (critical[i] == critical[best] && i < best)) best = i;
            }
            if (best >= 0) {
                int t = ops[best].type;
                picked[t - OP_ALU] = best;
                used_type[t] = 1;
                if (t == OP_ALU) b.alu = ops[best];
                else if (t == OP_MUL) b.mul = ops[best];
                else b.mem = ops[best];
            }
        }

        out[cycle] = b;
        int any = 0;
        for (int s = 0; s < 3; ++s) if (picked[s] >= 0) {
            int u = picked[s]; any = 1; done[u] = 1; --remaining;
            for (int e = head[u]; e >= 0; e = edges[e].next) {
                int v = edges[e].to;
                if (release[v] < cycle + edges[e].delay) release[v] = cycle + edges[e].delay;
                if (--indeg[v] == 0) { /* release already contains latency */ }
            }
        }
        ++cycle;
        (void)any; /* a valid DAG always has a ready node; idle cycles are legal */
    }

    free(head); free(indeg); free(last); free(rhead); free(rnext);
    free(readers); free(edges); free(critical); free(done); free(release);
    return cycle;
}

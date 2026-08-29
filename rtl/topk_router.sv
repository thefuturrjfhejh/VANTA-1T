// Pedagogical top-k router. Defaults are deliberately tiny for inspection.
module topk_router #(
    parameter int EXPERTS = 16,
    parameter int TOP_K = 2,
    parameter int SCORE_W = 16,
    parameter int ID_W = $clog2(EXPERTS)
) (
    input  logic signed [SCORE_W-1:0] score_i[EXPERTS],
    output logic [ID_W-1:0]           expert_id_o[TOP_K],
    output logic signed [SCORE_W-1:0] expert_score_o[TOP_K]
);
    integer e;
    integer k;
    logic signed [SCORE_W-1:0] candidate_score;
    logic [ID_W-1:0] candidate_id;

    always_comb begin
        for (k = 0; k < TOP_K; k = k + 1) begin
            expert_score_o[k] = {1'b1, {(SCORE_W-1){1'b0}}};
            expert_id_o[k] = '0;
        end

        for (e = 0; e < EXPERTS; e = e + 1) begin
            candidate_score = score_i[e];
            candidate_id = e[ID_W-1:0];
            for (k = 0; k < TOP_K; k = k + 1) begin
                if (candidate_score > expert_score_o[k]) begin
                    for (int shift = TOP_K - 1; shift > k; shift = shift - 1) begin
                        expert_score_o[shift] = expert_score_o[shift - 1];
                        expert_id_o[shift] = expert_id_o[shift - 1];
                    end
                    expert_score_o[k] = candidate_score;
                    expert_id_o[k] = candidate_id;
                    candidate_score = {1'b1, {(SCORE_W-1){1'b0}}};
                end
            end
        end
    end
endmodule

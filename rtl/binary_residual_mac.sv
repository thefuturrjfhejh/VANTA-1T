// Pedagogical RTL: one binary-backbone dot product plus signed residual.
// This is intentionally small and readable; production logic would be deeply
// pipelined, grouped, and generated from physical SRAM/HBM interfaces.
module binary_residual_mac #(
    parameter int LANES = 16,
    parameter int ACT_W = 8,
    parameter int RES_W = 4,
    parameter int ACC_W = 32
) (
    input  logic                         clk,
    input  logic                         rst_n,
    input  logic                         valid_i,
    input  logic signed [ACT_W-1:0]      act_i [LANES],
    input  logic                         sign_i[LANES],
    input  logic signed [RES_W-1:0]      residual_i[LANES],
    input  logic                         residual_valid_i[LANES],
    output logic                         valid_o,
    output logic signed [ACC_W-1:0]      sum_o
);
    integer lane;
    logic signed [ACC_W-1:0] next_sum;

    always_comb begin
        next_sum = '0;
        for (lane = 0; lane < LANES; lane = lane + 1) begin
            if (sign_i[lane]) begin
                next_sum = next_sum + act_i[lane];
            end else begin
                next_sum = next_sum - act_i[lane];
            end
            if (residual_valid_i[lane]) begin
                next_sum = next_sum + act_i[lane] * residual_i[lane];
            end
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid_o <= 1'b0;
            sum_o <= '0;
        end else begin
            valid_o <= valid_i;
            if (valid_i) begin
                sum_o <= next_sum;
            end
        end
    end
endmodule

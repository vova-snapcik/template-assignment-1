## Analysis of the Multi-Objective Trade-Off (Question 1.ii)

This table represents the **Pareto Frontier**, generated using the $\epsilon$-Constraint method, which shows the optimal trade-off between minimizing **Energy Procurement Cost** ($J_{\text{cost}}$) and minimizing **Discomfort** ($J_{\text{discomfort}}$).

The problem was solved by setting the primary objective to cost minimization, subject to an upper bound on discomfort:

$$\min J_{\text{cost}} \quad \text{s.t.} \quad J_{\text{discomfort}} \le \epsilon_{\text{discomfort}}$$

Where the discomfort objective is the squared deviation from the reference load:
$$J_{\text{discomfort}} = \sum_{t=1}^{T} (P^{\text{flex}}_t - P^{\text{ref}}_t)^2$$

***

### 1. The Cost vs. Discomfort Trade-Off

The results clearly illustrate the trade-off inherent in the problem:

| Observation | Implication |
| :--- | :--- |
| **High Cost ($65.51 \text{ DKK}$)** | Occurs when Discomfort is minimized ($\epsilon \approx 3.76$). The consumer must pay a high price to strictly adhere to the reference load schedule. |
| **Low Cost ($0.00 \text{ DKK}$)** | Occurs when Discomfort is maximized ($\epsilon \ge 30.05$). Allowing maximum flexibility lets the consumer achieve the absolute minimum procurement cost (a net profit or zero cost in this case). |

***

### 2. Efficiency and Binding Constraints

The relationship between the `Target $\epsilon$` (the constraint) and the `Actual Discomfort` (the result) indicates the efficiency of the solution:

* **Solutions 1-7 (Binding Constraint):** For these points, the **Actual Discomfort is equal to the Target $\epsilon$**. This means the constraint was **active**, and the solution lies perfectly on the Pareto frontier.
* **Solutions 8-9 (Non-Binding Constraint):** For these points, the **Actual Discomfort is less than the Target $\epsilon$**. This indicates the **cost has reached its minimum possible value** ($0.00 \text{ DKK}$), and increasing the $\epsilon$ target further provides no additional cost savings.

***

### 3. Conclusion for Decision-Making

The consumer should focus on the trade-off curve's diminishing returns. A good compromise might be the solution where **Actual Discomfort $\approx 26.29$** for a cost of **$3.9164 \text{ DKK}$**, as it is very close to the minimum cost while requiring less schedule disruption than the absolute maximum flexibility scenario.
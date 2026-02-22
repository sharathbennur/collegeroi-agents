export interface YearlyTuitionData {
    tuition: number;
    roomBoard: number;
    financialAid: number;
}

export interface TaxRates {
    federal: number;
    state: number;
    medicare: number;
    socialSecurity: number;
    city: number;
}

export interface MonthlyExpenses {
    rent: number;
    groceries: number;
    eatingOut: number;
    utilities: number;
    transportation: number;
    healthCare: number;
    miscellaneous: number;
    contribution401k: number;
}

export interface CalculationInput {
    collegeName: string;
    fourYearTuitionTotal: number;
    fourYearFinancialAidTotal: number;
    annualFamilyContribution: number;
    loanInterestRate: number;
    loanTermYears: number;
    annualGrossSalary: number;
    inflationRate: number;

    // Breakdowns
    tuitionBreakdown: {
        year1: YearlyTuitionData;
        year2: YearlyTuitionData;
        year3: YearlyTuitionData;
        year4: YearlyTuitionData;
    };
    taxRates: TaxRates;
    expensesBreakdown: MonthlyExpenses;
}

export interface CalculationOutput {
    // Cost Metrics
    fourYearCost: number;
    fourYearAid: number;
    fourYearFamilyContribution: number;
    totalCostOfCollege: number; // Includes interest

    // Loan Metrics
    loanAmount: number;
    monthlyPayment: number;
    totalInterestPaid: number;

    // Cash Flow Metrics (Monthly)
    monthlyGross: number;
    monthlyTax: number;
    monthlyTakeHome: number;
    netMonthlyCashFlow: number;

    // ROI Metrics (10-Year)
    tenYearAccumulatedNetCashFlow: number;
    tenYearTotal401kContribution: number;
    totalTenYearProjectedSavings: number;
}

export interface SharedScenario {
    input: CalculationInput;
    output: CalculationOutput;
    version: string;
    timestamp: string;
}

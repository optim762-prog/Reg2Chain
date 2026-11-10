// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RefinedOliveOilCompliance {
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 300;
        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 5000;
        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 1250;
        // source: Annex I, Table A, row 4
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 160;

        return true;
    }

    function checkLabelling(string[] memory items) public pure returns (bool) {
        // source: Class hierarchy (⊑ = subClassOf): - RefinedOliveOil ⊑ OliveOils ⊑ Oils ⊑ Fats ⊑ Product
        // source: Object properties (domain -> range): - requiresLabelItem (OBLIGATION): Product -> LabelItem
        // source: Object properties (domain -> range): - permitsLabelItem (PERMISSION): Product -> LabelItem
        // source: Object properties (domain -> range): - prohibitsLabelItem (PROHIBITION): Product -> LabelItem
        // source: Object properties (domain -> range): - hasLimit (LIMIT): Product -> Threshold (value + parameter)
        // source: Object properties (domain -> range): - hasCondition (CONDITION): LabelItem -> Condition
        // source: Object properties (domain -> range): - refersTo (REFERS_TO): Product -> LegalReference

        // Implement the labelling checks here based on the ontology excerpt

        return true;
    }

    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items)
        public pure returns (bool) {
        if (parameters.length != values.length) return false;
        for (uint256 i = 0; i < parameters.length; i++) {
            if (!checkLimit(parameters[i], values[i])) return false;
        }
        return checkLabelling(items);
    }
}

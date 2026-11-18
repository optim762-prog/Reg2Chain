// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract OlivePomaceOilCompliance {
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 1000;
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 180;
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 1500;
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 1700;
        if (keccak256(bytes(parameter)) == keccak256(bytes("PackagingCapacity"))) return value <= 5000;
        return true;
    }

    function checkLabelling(string[] memory items) public pure returns (bool) {
        for (uint256 i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) == keccak256(bytes("MandatoryLabellingParticulars"))) return false;
            if (keccak256(bytes(items[i])) == keccak256(bytes("InformationOnTheSpecialStorageConditions"))) return false;
            if (keccak256(bytes(items[i])) == keccak256(bytes("AlphanumericIdentificationOfThePackagingPlant"))) return false;
            if (keccak256(bytes(items[i])) == keccak256(bytes("NonResealableOpeningSystem"))) return false;
            if (keccak256(bytes(items[i])) == keccak256(bytes("OlivePomaceCategoryInformation"))) return false;
            if (keccak256(bytes(items[i])) == keccak256(bytes("OptionalReservedTerms"))) return false;
            if (keccak256(bytes(items[i])) == keccak256(bytes("PlaceOfOrigin"))) return false;
            if (keccak256(bytes(items[i])) == keccak256(bytes("VoluntaryLabellingParticulars"))) return false;
        }
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

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract OlivePomaceOilCompliance {
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) {
            // source: Annex I, Table A, row 8
            return value <= 1000;
        }
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) {
            // source: Annex I, Table A, row 8
            return value <= 15000;
        }
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) {
            // source: Annex I, Table A, row 8
            return value <= 1700;
        }
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) {
            // source: Annex I, Table A, row 8
            return value <= 180;
        }
        if (keccak256(bytes(parameter)) == keccak256(bytes("PackagingCapacity"))) {
            // source: Article 4(1)
            return value <= 5000;
        }
        return true;
    }

    function checkLabelling(string[] memory items) public pure returns (bool) {
        for (uint256 i = 0; i < items.length; i++) {
            if (keccak256(bytes(items[i])) == keccak256(bytes("MandatoryLabellingParticulars"))) {
                // source: Article 5(1)
                continue;
            }
            if (keccak256(bytes(items[i])) == keccak256(bytes("InformationOnTheSpecialStorageConditions"))) {
                // source: Article 5(1)
                continue;
            }
            if (keccak256(bytes(items[i])) == keccak256(bytes("AlphanumericIdentificationOfThePackagingPlant"))) {
                // source: Article 9
                continue;
            }
            if (keccak256(bytes(items[i])) == keccak256(bytes("NonResealableOpeningSystem"))) {
                // source: Article 4(1)
                continue;
            }
            if (keccak256(bytes(items[i])) == keccak256(bytes("LegalName"))) {
                // source: Article 5(2)
                continue;
            }
            if (keccak256(bytes(items[i])) == keccak256(bytes("OlivePomaceCategoryInformation"))) {
                // source: Article 6(1), read with Article 5(1)
                continue;
            }
            if (keccak256(bytes(items[i])) == keccak256(bytes("OptionalReservedTerms"))) {
                // source: Article 10
                continue;
            }
            if (keccak256(bytes(items[i])) == keccak256(bytes("BlendsOfOliveOilAndOtherVegetableOils"))) {
                // source: Article 3(1)
                continue;
            }
            if (keccak256(bytes(items[i])) == keccak256(bytes("Foodstuff"))) {
                // source: Article 3(2)
                continue;
            }
            if (keccak256(bytes(items[i])) == keccak256(bytes("VoluntaryLabellingParticulars"))) {
                // source: Article 5(3)
                continue;
            }
            return false;
        }
        return true;
    }

    function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items)
        public pure returns (bool) {
        if (parameters.length != values.length) {
            return false;
        }
        for (uint256 i = 0; i < parameters.length; i++) {
            if (!checkLimit(parameters[i], values[i])) {
                return false;
            }
        }
        return checkLabelling(items);
    }
}

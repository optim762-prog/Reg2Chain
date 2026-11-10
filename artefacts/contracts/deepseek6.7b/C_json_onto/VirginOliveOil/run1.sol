// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VirginOliveOilCompliance {
    function checkLimit(string memory parameter, int256 value) public pure returns (bool) {
        // source: Annex I, Table A, row 2
        if (keccak256(bytes(parameter)) == keccak256(bytes("Acidity"))) return value <= 2000;
        // source: Annex I, Table A, row 2
        if (keccak256(bytes(parameter)) == keccak256(bytes("PeroxideValueMEqO2Kg"))) return value <= 20000;
        // source: Annex I, Table A, row 2
        if (keccak256(bytes(parameter)) == keccak256(bytes("K232"))) return value <= 2600;
        // source: Annex I, Table A, row 2
        if (keccak256(bytes(parameter)) == keccak256(bytes("K268OrK270"))) return value <= 250;
        // source: Annex I, Table A, row 2
        if (keccak256(bytes(parameter)) == keccak256(bytes("DeltaK"))) return value <= 100;
        // source: Annex I, Table A, row 2
        if (keccak256(bytes(parameter)) == keccak256(bytes("MedianOfDefectMd"))) return value <= 3500;
        // source: Annex I, Table A, row 2
        if (keccak256(bytes(parameter)) == keccak256(bytes("FruityMedianMf"))) return value > 0;
        // source: Annex I, Table A, row 2
        if (keccak256(bytes(parameter)) == keccak256(bytes("PackagingCapacity"))) return value <= 5000;

        return true;
    }

    function checkLabelling(string[] memory items) public pure returns (bool) {
        // source: Article 5(1)
        if (!contains(items, "MandatoryLabellingParticulars")) return false;
        // source: Article 7
        if (!contains(items, "InformationOnTheSpecialStorageConditions")) return false;
        // source: Article 9
        if (!contains(items, "AlphanumericIdentificationOfThePackagingPlant")) return false;
        // source: Article 8(1)
        if (!contains(items, "PlaceOfOrigin")) return false;
        // source: Article 4(1)
        if (!contains(items, "NonResealableOpeningSystem")) return false;
        // source: Article 6(1), read with Article 5(1)
        if (!contains(items, "LegalName")) return false;
        // source: Article 6(2)(b)
        if (!contains(items, "OliveOilObtainedDirectlyFromOlivesAndSolelyByMechanicalMeans")) return false;

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

    function contains(string[] memory arr, string memory str) private pure returns (bool) {
        for (uint256 i = 0; i < arr.length; i++) {
            if (keccak256(bytes(arr[i])) == keccak256(bytes(str))) return true;
        }
        return false;
    }
}

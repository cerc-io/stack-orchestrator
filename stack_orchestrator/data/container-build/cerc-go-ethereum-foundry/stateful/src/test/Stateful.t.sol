// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.10;

import "ds-test/test.sol";
import {Stateful} from "../Stateful.sol";

contract StatefulTest is DSTest {
    Stateful contractA;
    //contractA A;
    uint x;
    function setUp() public {
        x = 1;
        contractA = new Stateful(x);
    }

    function testExample() public {
        contractA.off();
    }
}

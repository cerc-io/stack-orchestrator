// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.10;

contract Stateful {
  uint x;

  constructor(uint y) public {
    x = y;
  }

  function off() public {
    require(x == 1);
    x = 0;
  }

  function on() public {
    require(x == 0);
    x = 1;
  }
  function inc() public {
    x = x + 1;
  }
}

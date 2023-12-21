// SPDX-License-Identifier: MIT 
pragma solidity >= 0.6.2 <0.9.0;

/*
    CS61065: Theory and Applications of Blockchain
    Assignment 1: Ethereum Basics

    19EC39007: Bbiswabasu Roy
    19EC39044: Ujwal Nitin Nayak
    19EC39045: Rishi Suman

    Deployment details:
    1. Smart contract address: 0x42d1feb8f019bd7ca2929400549b0119d1cefd95
    2. Total number of seats (quota): 50
    3. Price per ticket (price): 1000
*/

contract TicketBooking {
    /* Buyer structure */
    struct Buyer {
        uint256 totalPrice;
        uint256 numTickets;
        string email;
    }
    address public owner;
    uint256 public numTicketsSold;
    uint256 public quota;
    uint256 public price;
    mapping(address => Buyer) BuyersPaid;

    /* Constructor */
    constructor(uint256 _quota, uint256 _price) {
        owner = msg.sender;
        numTicketsSold = 0;
        quota = _quota;
        price = _price;
    }

    /* Modifies functions to continue operation based on seats left */
    modifier soldOut() {
        require(numTicketsSold < quota, "All tickets have been sold");
        _;
    }

    /* 
       Allows buyer to buy tickets that can be bought based on availability and
       the proposed value
    */
    function buyTicket(string memory email, uint256 numTickets) public payable soldOut
    {
        uint256 ticketsBought=0;
        if (numTickets + numTicketsSold <= quota)
            ticketsBought = numTickets;
        else 
            ticketsBought = quota-numTicketsSold;
        
        if (msg.value/price < ticketsBought)
            ticketsBought = msg.value/price;

        uint256 refund = msg.value - ticketsBought*price;
        if (BuyersPaid[msg.sender].numTickets > 0) {
            BuyersPaid[msg.sender].numTickets += ticketsBought;
            BuyersPaid[msg.sender].totalPrice += price * ticketsBought;
        } else {
            BuyersPaid[msg.sender].email = email;
            BuyersPaid[msg.sender].numTickets = ticketsBought;
            BuyersPaid[msg.sender].totalPrice = price * ticketsBought;
        }

        numTicketsSold += ticketsBought;
        payable(msg.sender).transfer(refund);
    }

    /* Modifies functions to allow invocation by owner only */
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can send the transaction");
        _;
    }

    /* Transfers the total contract amount to the owner */
    function withdrawFunds() public onlyOwner {
        payable(owner).transfer(address(this).balance);
    }

    /* Refunds the total amount paid by the buyer */
    function refundTicket(address buyer) public onlyOwner {
        payable(buyer).transfer(BuyersPaid[buyer].totalPrice);
        numTicketsSold -= BuyersPaid[buyer].numTickets;
        delete BuyersPaid[buyer];
    }

    /* Returns amount paid by the buyer */
    function getBuyerAmountPaid(address buyer) public view returns (uint256) {
        return BuyersPaid[buyer].totalPrice;
    }

    /* Returns the number of tickets sold */
    function getNumTicketsSold() public view returns (uint256) {
        return numTicketsSold;
    }
    
    /* Kills the contract */
    function kill() public onlyOwner {
        selfdestruct(payable(owner));
    }
}

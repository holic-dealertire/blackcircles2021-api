SELECT io_size, io_size_origin, io_part_no, io_pr, io_max_weight, io_speed, io_car, io_oe, io_car_type, io_tire_type, io_factory_price, io_maker, it_name, it_pattern, it_season, it_performance_type, delivery_stock, price, io_discontinued
FROM (SELECT io_no, it_id AS io_it_id, io_size, io_part_no, io_size_origin, io_pr, io_max_weight, io_speed, io_car, io_oe, io_tire_type, io_factory_price, io_maker, io_car_type, sell_cnt, io_btob_lowest, io_btob_price, io_discontinued, io_delivery_price FROM g5_shop_item_option where io_no = '" + io_no + "') opt
         LEFT JOIN (SELECT it_id, ca_id AS item_ca_id FROM g5_shop_item) item ON item.it_id = cart.cart_it_id
         LEFT JOIN
(select *
 from (select *, sum(sum_stock) as delivery_stock
       from (SELECT *
             FROM (SELECT *,
                       CASE
                           WHEN sale_delivery >= '" + retail_type + "' + 2
                               THEN '" + retail_type + "'
                           WHEN sale_delivery >= '" + retail_type + "' - range_1 + 2 AND sale_delivery < '" + retail_type + "' + 2
                               THEN '" + retail_type + "' - range_1
                           WHEN sale_delivery >= '" + retail_type + "' - range_1 - range_2 + 2 AND sale_delivery < '" + retail_type + "' - range_1 + 2
                               THEN '" + retail_type + "' - range_1 - range_2
                           WHEN sale_delivery >= '" + retail_type + "' - range_1 - range_2 - range_3 + 2 AND sale_delivery < '" + retail_type + "' - range_1 - range_2 + 2
                               THEN '" + retail_type + "' - range_1 - range_2 - range_3
                           else sale_delivery - 2
                           end AS price
                   FROM (SELECT *,
                             Sum(stock) AS sum_stock
                         FROM (SELECT io_no AS stock_io_no, sale_delivery, stock, mb_no AS stock_mb_no, idx as delivery_idx
                               FROM tbl_item_option_price_stock
                               WHERE stock > 0) stock
                                  LEFT JOIN (SELECT io_no AS check_io_no, it_id AS check_io_it_id, io_sell_price_basic, io_sell_price_premium
                                             FROM g5_shop_item_option
                                             WHERE origin_io_no IS NULL) check_option
                         ON stock.stock_io_no = check_option.check_io_no
                                  LEFT JOIN (SELECT it_id AS check_it_id, ca_id AS check_it_ca_id
                                             FROM g5_shop_item) check_item
                         ON check_item.check_it_id = check_option.check_io_it_id
                                  LEFT JOIN (SELECT ca_id as ca_id_1, range_1, range_2, range_3
                                             FROM g5_shop_category) cate
                         ON cate.ca_id_1 = check_item.check_it_ca_id
                                  LEFT JOIN (SELECT ca_id AS contract_ca_id, mb_no AS contract_mb_no, idx
                                             FROM tbl_member_seller_item_contract
                                             WHERE contract_status = '1' AND contract_start <= '" + nowDate + "' AND contract_end >= '" + nowDate + "') contract
                         ON contract.contract_ca_id = check_item.check_it_ca_id AND contract.contract_mb_no = stock.stock_mb_no
                         WHERE contract.idx IS NOT NULL
                         GROUP BY stock_io_no, sale_delivery) stock) AS price_table
             WHERE price IS NOT NULL
             ORDER BY stock_io_no ASC, price DESC) as stock
       group by stock_io_no, price
       order by price desc) price
 group by stock_io_no) AS delivery_price
ON delivery_price.stock_io_no = opt.io_no